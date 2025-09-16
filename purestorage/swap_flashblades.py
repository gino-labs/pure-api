#!/usr/bin/env python3
import purefb_api as pfa
import purefb_log as pfl
import subprocess
import tempfile
import time
import json
import os

# Logger object
scriptlog = pfl.PureLog()

# FlashBlade API Object Instances
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

# Get Legacy file systems
legacy_filesystems = legacy.get_filesystems()

# Get S200 file systems
s200_filesystems = s200.get_filesystems()

s200_filesystem_names = [fs["name"] for fs in s200_filesystems]

scriptlog.write_log("S200 file system names list", jsondata=s200_filesystem_names, show_output=True)

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

# Get active NFS clients before swapping
scriptlog.write_log("Retrieving active NFS clients from Legacy FlashBlade. Reload Cache in progress...", show_output=True)
hosts = legacy.get_nfs_clients()

# Create inventory file with NFS clients obtained

inventory = {
    "all": {
        "hosts": {host["name"].split(":")[0]: None for host in hosts["items"] if "172.20.0" not in host}
    }
}

inventory_filename = s200.mgt_ip[:2] + "_inventory.json"

os.makedirs("logs", exist_ok=True)
with open(f"logs/{inventory_filename}", "w") as inv_file:
    json.dump(inventory, inv_file, indent=4)

# Create final snapshots on Legacy and wait 30 seconds for them to settle

# Demote / Disable each file system on Legacy (Handle exception: non-replication snapshot error, skip demotion)

# Patch Legacy IPs to S200

# Patch S200 IPs to Legacy

# Delete replica links on Legacy

# Promote / Enabled each file system on S200

# Run ansible playbook with nfs client inventory and production IP variable

# Clean up
