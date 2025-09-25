#!/usr/bin/env python3
import purefb_api as pfa
from purefb_log import *
import subprocess
import time
import json
import os

# Logger object
scriptlog = PureLog()

# Initialize Stopwatch object then start
timer = Stopwatch()
timer.start_stopwatch()

# FlashBlade API Object Instances
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

# Get Legacy file systems
legacy_filesystems = legacy.get_filesystems()

# Get S200 file systems
s200_filesystems = s200.get_filesystems()

s200_promo_payloads = {}
for fs in legacy_filesystems:
    s200_promo_payloads[fs["name"]] = {
        "nfs": {
            "v3_enabled": fs["nfs"]["v3_enabled"],
            "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
            "rules": fs["nfs"]["rules"]
        },
        "http": {
            "enabled": fs["http"]["enabled"]
        },
        "writable": True,
        "requested_promotion_state": "promoted" 
    }

scriptlog.write_log("S200 file system promotion data from legacy", jsondata=s200_promo_payloads, show_output=True)

# Get Legacy interfaces' info
legacy_interfaces = legacy.get_interfaces()

legacy_data_iface_names = []
legacy_data_ips = []

for iface in legacy_interfaces:
    if "data" in iface["services"]:
        legacy_data_iface_names.append(iface["name"])
        legacy_data_ips.append(iface["address"])

# Store Production IPs in variable to pass to ansible playbook later
if len(legacy_data_ips) > 1:
    production_ips = "|".join(legacy_data_ips)
elif len(legacy_data_ips) == 1:
    production_ips = legacy_data_ips[0]
else:
    print("No data interfaces.")
    print()

scriptlog.write_log("Legacy data interface names list", jsondata=legacy_data_iface_names, show_output=True)
scriptlog.write_log("Legacy production IP list", jsondata=legacy_data_ips, show_output=True)

# Get S200 interfaces' info
s200_interfaces = s200.get_interfaces()

s200_data_iface_names = [iface["name"] for iface in s200_interfaces if "data" in iface["name"]]
scriptlog.write_log("S200 data interface names list", jsondata=s200_data_iface_names, show_output=True)

# Get file system replica links on Legacy
legacy_replica_links = legacy.get_filesytem_replica_links()
replication_filesystems = [link["local_file_system"]["name"] for link in legacy_replica_links]

# Get active NFS clients before swapping
scriptlog.write_log("Retrieving active NFS clients from Legacy FlashBlade. Reload Cache in progress...", show_output=True)
hosts = legacy.get_nfs_clients()

# Create inventory file with NFS clients obtained

inventory = {
    "all": {
        "hosts": {host["name"].split(":")[0]: None for host in hosts["items"] if "172.20." not in host["name"]}
    }
}

inventory_filename = s200.mgt_ip[:2] + "_inventory.json"

os.makedirs("logs", exist_ok=True)
with open(f"logs/{inventory_filename}", "w") as inv_file:
    json.dump(inventory, inv_file, indent=4)

scriptlog.write_log(f"Inventory created with name logs/{inventory_filename}", jsondata=inventory, show_output=True)

# File systems that would be snapshotted
promoted_fs_list = []
for fs in legacy_filesystems:
    if fs["promotion_status"] == "promoted":
        promoted_fs_list.append(fs["name"])

scriptlog.write_log(f"File systems that would get pre-swap snapshot: {len(promoted_fs_list)}", jsondata=promoted_fs_list, show_output=True)

scriptlog.write_log("Waiting 30 seconds for pre-swap snapshots to settle...", show_output=True)
timer.countdown(30)
