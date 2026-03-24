import os
import yaml
import argparse
import subprocess

from everpure import FlashBladeAPI
from everpure import EnvironmentReader
from everpure import ApiError


### Setup ###

# Environment variables
gen1_vars = EnvironmentReader("FB1_NAME", "FB1_MGT", "FB1_TOKEN")
s200_vars = EnvironmentReader("FB2_NAME", "FB2_MGT", "FB2_TOKEN")

# FlashBlade API instances
gen1 = FlashBladeAPI(*gen1_vars)
s200 = FlashBladeAPI(*s200_vars)

# File systems
g1_filesystems = gen1.get_filesystems()
s2_filesystems = s200.get_filesystems()

# Network interfaces
g1_interfaces = gen1.get_network_interfaces()
s2_interfaces = s200.get_network_interfaces()

# Ansible
ansible_dir = '../ansible/'
os.makedirs(f"{ansible_dir}/inventory", exist_ok=True)
os.makedirs(f"{ansible_dir}/vars", exist_ok=True)
ansible_inv = f"{ansible_dir}/inventory/nfs_clients.yml"
ansible_pb = f"{ansible_dir}/remount-pure.yml"

# Migration details
migration_dir = f"{s200.name}_migration"
os.makedirs(migration_dir)
prod_ifaces_yaml = f"{migration_dir}/production_interfaces.yml"
second_ifaces_yaml = f"{migration_dir}/secondary_interfaces.yml"


### Functions ###

def take_snapshots():
    pass # TODO

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

def swap_production_vars_to_s200():
    with open(prod_ifaces_yaml, "r") as f:
        prod_ifaces = yaml.safe_load(f)
    with open(second_ifaces_yaml, "r") as f:
        second_ifaces = yaml.safe_load(f)

    if not prod_ifaces:
        raise ValueError(f"Empty production variables loaded from {prod_ifaces_yaml}")

    # Compare interfaces for matching vlans
    iface_patched = False
    for iface in prod_ifaces:
        if "data" not in iface["services"]:
            continue
        
        for iface2 in second_ifaces:
            # Patch if two interfaces have same vlan
            if iface["vlan"] == iface2["vlan"]:
                s200.patch_network_interfaces(iface2["name"], json={"address": iface["address"], "services": iface["services"]})
                gen1.patch_network_interfaces(iface["name"], json={"address": iface2["address"], "services": iface2["services"]})
                iface_patched = True

        if not iface_patched:
            s200.post_network_interfaces(iface["name"], json={"address": iface["address"], "services": iface["services"], "type": "vip" })
            gen1.delete_network_interfaces(iface["name"])
            iface_patched = False

def demote_gen1_filesystems():
    for fs in g1_filesystems:
        try:
            gen1.patch_filesystems(fs["name"], json={"writable": False,"requested_promotion_state": "demoted"})
        except ApiError:
            gen1.patch_filesystems(fs["name"], json={"writable": False})

def delete_replication_links():
    for link in gen1.get_filesystem_replica_links():
        fs = link["local_file_system"]["name"]
        remote = link["remote"]["name"]
        gen1.delete_filesystem_replica_links(fs, remote)

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

def remount_nfs_clients():
    with open(prod_ifaces_yaml, "r") as f:
        prod_ifaces = yaml.safe_load(f)
    pure_ips = "|".join([iface["address"] for iface in prod_ifaces])

    playbook = ["ansible-playbook", "-i", ansible_inv, "-e", f"pure_ips={pure_ips}", ansible_pb]
    print(f"Enter root password to run ansible playbook: {ansible_pb}")
    subprocess.run(playbook)


### Main ###

if __name__ == "__main__":
    pass # TODO

