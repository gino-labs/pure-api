#!/usr/bin/env python3
import purefb_api as pfa
import purefb_log as pfl
import subprocess
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
        "hosts": {host["name"].split(":")[0]: None for host in hosts["items"] if "172.20." not in host}
    }
}

inventory_filename = s200.mgt_ip[:2] + "_inventory.json"

os.makedirs("logs", exist_ok=True)
with open(f"logs/{inventory_filename}", "w") as inv_file:
    json.dump(inventory, inv_file, indent=4)

# Create final snapshots on Legacy and wait 30 seconds for them to settle
fs_snapshot_list = [fs["name"] for fs in legacy_filesystems if fs["promotion_status"] == "promoted"]
scriptlog.write_log("Create snapshots for promoted file systems and wait 30 seconds. (See JSON data)", jsondata=fs_snapshot_list, show_output=True)

# Demote / Disable each file system on Legacy (Handle exception: non-replication snapshot error, skip demotion)
demote_payload = {
    "writable": False,
    "requested_promotion_state": "demoted"
}
scriptlog.write_log("Using demote payload", jsondata=demote_payload, show_output=True)

fs_demote_list = [fs["name"] for fs in legacy_filesystems]
scriptlog.write_log("Demote Legacy filesystems, handle non replication snapshots.", jsondata=fs_demote_list, show_output=True)

# Patch Legacy IPs to S200
scriptlog.write_log("Patch Legacy IPs to S200.", show_output=True)
s200_new_ips = [iface["address"] for iface in legacy_interfaces if "data" in iface["services"]]

# Patch S200 IPs to Legacy
scriptlog.write_log("Patch S200 IPs to Legacy.", show_output=True)
legacy_new_ips = [iface["address"] for iface in s200_interfaces if "data" in iface["services"]]

ips_swapped = {
    "s200": s200_new_ips,
    "legacy": legacy_new_ips
}
scriptlog.write_log("New IPs that would be after swap.", jsondata=ips_swapped, show_output=True)

# Delete replica links on Legacy
fs_del_links_list = [link["local_file_system"]["name"] for link in legacy_replica_links]
scriptlog.write_log("Delete replica links on Legacy.", jsondata=fs_del_links_list, show_output=True)

# Promote / Enabled each file system on S200
promote_payload = {
    "nfs": {
        "v3_enabled": "enabled",
        "v4_1_enabled": "enabled",
        "rules": "(rules-here)"
    },
    "http": {
        "enabled": "disabled"
    },
    "writable": True,
    "requested_promotion_state": "promoted"
}

scriptlog.write_log("Using promote payload.", jsondata=promote_payload, show_output=True)

fs_promote_list = [fs["name"] for fs in s200_filesystems]
scriptlog.write_log("Promote S200 file systems.", show_output=True)

# Run ansible playbook with nfs client inventory and production IP variable
scriptlog.write_log(f"Simulate (ping only) runnning ansible playbook to handle remounting nfs clients in create inventory, pass egrep string: {production_ips}", jsondata=inventory, show_output=True)
print("Enter root password for ansible playbook.")
subprocess.run(["ansible", "all", "-i", f"logs/{inventory_filename}"], "-m", "ping")

# Clean up
scriptlog.write_log("Clean up, remove files if needed.", show_output=True)
