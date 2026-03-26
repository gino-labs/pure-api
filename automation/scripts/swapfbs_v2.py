#!/usr/bin/env python3
import os
import yaml
import argparse
import logging
import subprocess

from everpure import FlashBladeAPI
from everpure import EnvironmentReader
from everpure import ApiError


### Setup ###

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%m.%d-%H:%M:%S")
logger = logging.getLogger(__name__)

# Environment variables
gen1_vars = EnvironmentReader("FB1_NAME", "FB1_MGT", "FB1_TOKEN")
s200_vars = EnvironmentReader("FB2_NAME", "FB2_MGT", "FB2_TOKEN") 

# FlashBlade API instances
gen1 = FlashBladeAPI(*gen1_vars)
s200 = FlashBladeAPI(*s200_vars)
logger.info(f"FlashBladeAPI instances created for {gen1_vars.name} & {s200_vars.name}")

# File systems
g1_filesystems = gen1.get_filesystems()
s2_filesystems = s200.get_filesystems()
replication_links = gen1.get_filesystem_replica_links()
logger.info("File system data retrieved")

# Network interfaces
g1_interfaces = gen1.get_network_interfaces()
s2_interfaces = s200.get_network_interfaces()
logger.info("Network interfaces data retrieved")

# Ansible
ansible_dir = '../ansible/'
os.makedirs(f"{ansible_dir}/inventory", exist_ok=True)
os.makedirs(f"{ansible_dir}/vars", exist_ok=True)
ansible_inv = f"{ansible_dir}/inventory/nfs_clients.yml"
ansible_pb = f"{ansible_dir}/remount-pure.yml"
logger.info(f"Target ansible inventory for NFS clients: {ansible_inv}")
logger.info(f"Target ansible playbook to run: {ansible_pb}")

# Migration details
migration_dir = f"{s200.name}_migration"
os.makedirs(migration_dir)
prod_ifaces_yaml = f"{migration_dir}/production_interfaces.yml"
second_ifaces_yaml = f"{migration_dir}/secondary_interfaces.yml"
logger.info(f"Migration details dumped to {migration_dir}")


### Functions ###

def take_snapshots(suffix: str):
    filesystems = [fs["name"] for fs in g1_filesystems]
    replica_filesystems = [link["local_file_system"]["name"] for link in replication_links]
    
    for fs in filesystems:
        json = {"suffix": suffix}
        if fs in replica_filesystems:
            gen1.post_filesystem_snapshots(fs, json=json, send=True)
            logger.info(f"{suffix} replication snapshot created for {fs}")
        else:
            gen1.post_filesystem_snapshots(fs, json=json)
            logger.info(f"{suffix} snapshot created for {fs}")


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
        logger.info(f"NFS client inventory dumped to {ansible_inv}")

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
        logger.info(f"Production variables dumped to {prod_ifaces_yaml}")

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
        logger.info(f"Secondary variables dumped to {prod_ifaces_yaml}")

def demote_gen1_filesystems():
    for fs in g1_filesystems:
        try:
            gen1.patch_filesystems(fs["name"], json={"writable": False,"requested_promotion_state": "demoted"})
            logger.info(f"Gen1 file system {fs['name']} set to demoted and unwritable")
        except ApiError:
            gen1.patch_filesystems(fs["name"], json={"writable": False})
            logger.info(f"Gen1 file system {fs['name']} set to unwritable")

def delete_replication_links():
    for link in replication_links:
        fs = link["local_file_system"]["name"]
        remote = link["remote"]["name"]
        gen1.delete_filesystem_replica_links(fs, remote)
        logger.info(f"Replication link deleted for {fs}")

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
                logger.info(f"S200 patched network interface: {iface['address']} -> {iface2['name']}")
                gen1.patch_network_interfaces(iface["name"], json={"address": iface2["address"], "services": iface2["services"]})
                logger.info(f"Gen1 patched network interface: {iface2['address']} -> {iface['name']}")
                iface_patched = True
                
        if not iface_patched:
            s200.post_network_interfaces(iface["name"], json={"address": iface["address"], "services": iface["services"], "type": "vip" })
            logger.info(f"S200 created network interface: {iface['name']} | {iface['address']}")
            gen1.delete_network_interfaces(iface["name"])
            logger.info(f"Gen1 deleted network interface: {iface['name']}")
            iface_patched = False

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
        logger.info(f"S200 file system promoted: {fs['name']}")

def remount_nfs_clients():
    with open(prod_ifaces_yaml, "r") as f:
        prod_ifaces = yaml.safe_load(f)
    pure_ips = "|".join([iface["address"] for iface in prod_ifaces])

    logger.info(f"Run ansible playbook to umount nfs shares using {pure_ips} ... This clears stale handles and allows automounts.")
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
