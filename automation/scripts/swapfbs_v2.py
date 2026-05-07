#!/usr/bin/env python3
import os
import yaml
import argparse
import subprocess

from everpure import PureLogger
from everpure import FlashBladeAPI
from everpure import EnvironmentReader
from everpure import ApiError


### Setup ###

mainlogger = PureLogger("script")

# Environment variables
gen1_vars = EnvironmentReader("FB1_NAME", "FB1_MGT", "FB1_TOKEN")
s200_vars = EnvironmentReader("FB2_NAME", "FB2_MGT", "FB2_TOKEN") 

# FlashBlade API instances
gen1 = FlashBladeAPI(*gen1_vars)
s200 = FlashBladeAPI(*s200_vars)
mainlogger.log("FB instances created")

# File systems
g1_filesystems = gen1.get_filesystems()
gen1.log("Get filesystems")
s2_filesystems = s200.get_filesystems()
s200.log("Get filesystems")
replication_links = gen1.get_filesystem_replica_links()
gen1.log("Get replication links")

# Network interfaces
g1_interfaces = gen1.get_network_interfaces()
gen1.log("Get network interfaces")
s2_interfaces = s200.get_network_interfaces()
s200.log("Get network interfaces")

# Ansible
ansible_dir = '../ansible/'
os.makedirs(f"{ansible_dir}/inventory", exist_ok=True)
os.makedirs(f"{ansible_dir}/vars", exist_ok=True)
ansible_inv = f"{ansible_dir}/inventory/nfs_clients.yml"
ansible_pb = f"{ansible_dir}/remount-pure.yml"
mainlogger.log(f"Target ansible inventory for NFS clients: {ansible_inv}")
mainlogger.log(f"Target ansible playbook to run: {ansible_pb}")

# Migration details
migration_dir = f"{s200.name}_migration"
os.makedirs(migration_dir, exist_ok=True)
prod_ifaces_yaml = f"{migration_dir}/production_interfaces.yml"
second_ifaces_yaml = f"{migration_dir}/secondary_interfaces.yml"
mainlogger.log(f"Migration details dumped to {migration_dir}")


### Functions ###

def take_snapshots(suffix: str):
    filesystems = [fs["name"] for fs in g1_filesystems]
    replica_filesystems = [link["local_file_system"]["name"] for link in replication_links]
    
    for fs in filesystems:
        json = {"suffix": suffix}
        if fs in replica_filesystems:
            gen1.post_filesystem_snapshots(fs, json=json, send=True)
            gen1.log(f"{suffix} replication snapshot created for {fs}")
        else:
            gen1.post_filesystem_snapshots(fs, json=json)
            gen1.log(f"{suffix} snapshot created for {fs}")


def create_client_inventory():
    nfs_clients = gen1.get_clients()
    inventory = {
        "all": {
            "hosts": {}
        }
    }
    hosts = inventory["all"]["hosts"]

    for client in nfs_clients:
        client_addr = client["name"].split(":")[0]
        if "172.20." not in client_addr:
            hosts[client_addr] = None

    if hosts == {}:
        raise ValueError("Empty inventory")
    else:
        with open(ansible_inv, "w") as f:
            yaml.safe_dump(inventory, f, indent=2)
        mainlogger.log(f"NFS client inventory dumped to {ansible_inv}")

def dump_production_vars():
    prod_ifaces = []
    for iface in g1_interfaces:
        if "data" in iface["services"]:
            prod_ifaces.append(
                {
                "interface_name": iface["name"],
                "address": iface["address"],
                "subnet_name": iface["subnet"]["name"],
                "vlan": iface["vlan"]
                }
            )
    if prod_ifaces == []:
        raise ValueError("Empty productions variables list")
    else:
        with open(prod_ifaces_yaml, "w") as f:
            yaml.safe_dump(prod_ifaces, f, indent=2)
        mainlogger.log(f"Production variables dumped to {prod_ifaces_yaml}")

def dump_secondary_vars():
    second_ifaces = []
    for iface in s2_interfaces:
        if "data" in iface["services"]:
            second_ifaces.append(
                {
                "interface_name": iface["name"],
                "address": iface["address"],
                "subnet_name": iface["subnet"]["name"],
                "vlan": iface["vlan"]
                }
            )
    if second_ifaces == []:
        raise ValueError("Empty secondary variables list")
    else:
        with open(second_ifaces_yaml, "w") as f:
            yaml.safe_dump(second_ifaces, f, indent=2)
        mainlogger.log(f"Secondary variables dumped to {second_ifaces_yaml}")

def demote_gen1_filesystems():
    for fs in g1_filesystems:
        try:
            gen1.patch_filesystems(fs["name"], json={"writable": False,"requested_promotion_state": "demoted"})
            gen1.log(f"File system {fs['name']} set to demoted and unwritable")
        except ApiError:
            gen1.patch_filesystems(fs["name"], json={"writable": False})
            gen1.log(f"File system {fs['name']} set to unwritable")

def delete_replication_links():
    for link in replication_links:
        fs = link["local_file_system"]["name"]
        remote = link["remote"]["name"]
        gen1.delete_filesystem_replica_links(fs, remote)
        gen1.log(f"Replication link deleted for {fs}")

def swap_production_vars_to_s200():
    with open(prod_ifaces_yaml, "r") as f:
        prod_ifaces = yaml.safe_load(f)
    with open(second_ifaces_yaml, "r") as f:
        second_ifaces = yaml.safe_load(f)

    if not prod_ifaces:
        raise ValueError(f"Empty production variables loaded from {prod_ifaces_yaml}")

    # Compare interfaces for matching vlans
    for iface in prod_ifaces:
        iface_patched = False
        for iface2 in second_ifaces:
            # Patch if two interfaces have same vlan
            if iface["vlan"] == iface2["vlan"]:
                s200.patch_network_interfaces(iface2["name"], json={"address": iface["address"]})
                s200.log(f"Patched network interface: {iface['address']} -> {iface2['name']}")
                gen1.patch_network_interfaces(iface["name"], json={"address": iface2["address"]})
                gen1.log(f"Patched network interface: {iface2['address']} -> {iface['name']}")
                iface_patched = True
                break
                
        if not iface_patched:
            s200.post_network_interfaces(iface["name"], json={"address": iface["address"], "services": ["data"], "type": "vip" })
            s200.log(f"Created network interface: {iface['name']} | {iface['address']}")
            gen1.delete_network_interfaces(iface["name"])
            gen1.log(f"Deleted network interface: {iface['name']}")

def promote_s200_flashblade():
    for fs in s2_filesystems:
        promo_payload = {
            "nfs": {
                "v3_enabled": fs["nfs"]["v3_enabled"],
                "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
                "rules": fs["nfs"]["rules"]
            },
            "writable": True,
            "requested_promotion_state": "promoted"
        }
        s200.patch_filesystems(fs["name"], json=promo_payload)
        s200.log(f"File system promoted: {fs['name']}")

def remount_nfs_clients():
    with open(prod_ifaces_yaml, "r") as f:
        prod_ifaces = yaml.safe_load(f)
    pure_ips = "|".join([iface["address"] for iface in prod_ifaces])

    mainlogger.log(f"Run ansible playbook to umount nfs shares using {pure_ips} ... This clears stale handles and allows automounts.")
    playbook = ["ansible-playbook", "-i", ansible_inv, "-e", f"pure_ips={pure_ips}", ansible_pb]
    print(f"Enter root password to run ansible playbook: {ansible_pb}")
    subprocess.run(playbook)


### Main ###

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=str)
    args = parser.parse_args()
    
    if args.snapshot:
       take_snapshots("pre-migration")
    else:
        create_client_inventory()
        dump_production_vars()
        dump_secondary_vars()
        demote_gen1_filesystems()
        delete_replication_links()
        swap_production_vars_to_s200()
        promote_s200_flashblade()
        remount_nfs_clients()
    mainlogger.log("Swap complete.")
