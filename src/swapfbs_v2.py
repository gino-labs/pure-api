#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
import subprocess
import yaml
import json
import os

# Initialize site variables and FB instances
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

# Get Filesystem info
legacy_filesystems = legacy.get_filesystems()["items"]
s200_filesystems = s200.get_filesystems()["items"]

# Replication info
replication_links = legacy.get_filesystem_replica_links()["items"]
replication_filesystems = [ link["local_file_system"]["name"] for link in replication_links ]

# Get interface info
legacy_interfaces = legacy.get_interfaces()["items"]
s200_interfaces = s200.get_interfaces()["items"]

# Filepath variables
inventory_file = "ansible/inventory/nfs_clients.yml"
vars_file = "ansible/vars/swap_vars.yml"

# Take snapshots prior to swap
def take_snapshots():
    for fs in legacy_filesystems:
        try:
            if fs["promotion_status"] == "promoted":
                legacy.post_filesystem_snapshot(fs["name"], "pre-swap")
        except ApiError as e:
            try:
                legacy.post_filesystem_snapshot(fs["name"], "pre-swap", replicate=False) # Non-replication snapshot
            except ApiError as e:
                pass
    time.sleep(20) # Wait time for snapshots to settle

# Capture connected NFS clients into a inventory file
def create_client_inventory():
    try:
        nfs_clients = legacy.get_nfs_clients()["items"]
        inventory = {
            "all": {
                "hosts": {}
            }
        }
        for client in nfs_clients:
            client_addr = client["name"].split(":")[0]
            if "172.20." not in client_addr:
                inventory["all"]["hosts"][client_addr] = None

        with open(inventory_file, "w") as f:
            yaml.safe_dump(inventory, f, indent=2)

        # TODO Validate YAML Inventory File

    except ApiError as e:
        e.check_details()

# Capture production IP's into a vars file
def save_swap_vars():
    swap_vars = {
        "production": [],
        "secondary": []
    }
    for interface in legacy_interfaces:
        if "data" in interface["services"]:
            dict_item = {
                "interface_name": interface["name"],
                "address": interface["address"],
                "subnet_name": interface["subnet"]["name"],
                "vlan": interface["vlan"] 
            }
            swap_vars["production"].append(dict_item)

    for interface in s200_interfaces:
        if "data" in interface["services"]:
            dict_item = {
                "interface_name": interface["name"],
                "address": interface["address"],
                "subnet_name": interface["subnet"]["name"],
                "vlan": interface["vlan"] 
            }
            swap_vars["secondary"].append(dict_item)

    with open(vars_file, "w") as f:
        yaml.safe_dump(swap_vars, f, indent=2)

    # TODO Validate YAML Vars File

# Demote Legacy Filesystems
def demote_legacy_filesystems():
    for fs in legacy_filesystems:
        try:
            demote_payload = {
                "writable": False,
                "requested_promotion_state": "demoted"
            }
            legacy.patch_filesystem(fs["name"], demote_payload)
        except ApiError:
            try:
                no_write_payload = { "writable": False }
                legacy.patch_filesystem(fs["name"], no_write_payload)
            except ApiError as e:
                e.check_details()

# Swap Production IPs to S200
def swap_production_ips_to_s200():
    # Find a matching subnet
    with open(vars_file, "r") as f:
        swap_vars = yaml.safe_load(f)

    for product in swap_vars["production"]:
        production_ip = { "address": product["address"] }
        # Check if production interface has a matching interface on secondary
        match = False
        for second in swap_vars["secondary"]:
            if product["name"] == second["name"] or product["subnet"] == second["subnet"]:
                secondary_ip = { "address": second["address"] }
                try:
                    s200.patch_interface(second["name"], production_ip)
                    legacy.patch_interface(product["name"], secondary_ip)
                except ApiError as e:
                    e.check_details()
                match = True
                break
        # Create production interface on s200
        if not match:
            production_info = {
                "address": product["address"],
                "services": [
                    "data"
                ],
                "type": "vip"
            }
            try:
                # Post to S200 and Delete from Legacy
                s200.post_interface(product["name"], production_info)
                legacy.delete_interface(product["name"])
            except ApiError as e:
                e.check_details()

# Promote S200 Filesystems
def promote_s200_filesystems():
    # Assumming 1 to 1 match of filesystem names
    for fs in legacy_filesystems:
        try:
            promote_payload = {
                "nfs": {
                    "v3_enabled": fs["nfs"]["v3_enabled"],
                    "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
                    "rules": fs["nfs"]["rules"]
                },
                "writable": True,
                "requested_promotion_state": "promoted" 
            }
            s200.patch_filesystem(fs["name"], promote_payload)
        except ApiError as e:
            e.check_details()

# Delete Replication links
def delete_replication_links():
    for link in replication_links:
        fs = link["local_file_system"]["name"]
        remote = link["remote"]["name"]
        try:
            legacy.delete_filesystem_replica_link(fs, remote)
        except ApiError as e:
            e.check_details()

# Run Ansible playbook with inventory of clients and variables captured
playbook = ["ansible-playbook", "-i", inventory_file, "-k", "remount-pure.yml"]
print("Enter root password for ansible playbook.")
subprocess.run(playbook, cwd="ansible")


