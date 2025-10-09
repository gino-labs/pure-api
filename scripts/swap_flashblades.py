#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
import subprocess
import json
import os

# Logger object #
logger = PureLog()

# Initialize Stopwatch object then start #
timer = Stopwatch()
timer.start_stopwatch()

# Environment variables sourced from shell (site specific)
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# FlashBlade API Object Instances #
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

# Get Legacy file systems #
legacy_filesystems = legacy.get_filesystems()

# Get S200 file systems #
s200_filesystems = s200.get_filesystems()

# Create promotion payloads using corresponding legacy file system
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

logger.write_log("S200 file system promotion data from legacy", jsondata=s200_promo_payloads)

# Get Legacy interfaces' info #
legacy_interfaces = legacy.get_interfaces()

legacy_data_iface_names = []
legacy_data_ips = []

for iface in legacy_interfaces:
    if "data" in iface["services"]:
        legacy_data_iface_names.append(iface["name"])
        legacy_data_ips.append(iface["address"])

# Store Production IPs in variable to pass to ansible playbook later #
if len(legacy_data_ips) > 1:
    production_ips = "|".join(legacy_data_ips)
elif len(legacy_data_ips) == 1:
    production_ips = legacy_data_ips[0]
else:
    print("No data interfaces.")
    print()

logger.write_log("Legacy data interface names list", jsondata=legacy_data_iface_names)
logger.write_log("Legacy production IP list", jsondata=legacy_data_ips)

# Get S200 interfaces' info #
s200_interfaces = s200.get_interfaces()

s200_data_iface_names = [iface["name"] for iface in s200_interfaces if "data" in iface["services"]]
logger.write_log("S200 data interface names list", jsondata=s200_data_iface_names)

# Get file system replica links on Legacy #
legacy_replica_links = legacy.get_filesytem_replica_links()

# Get active NFS clients before swapping #
logger.write_log("Retrieving active NFS clients from Legacy FlashBlade. Reload Cache in progress...", show_output=True)
hosts = legacy.get_nfs_clients()

# Create inventory file with NFS clients obtained #
inventory = {
    "all": {
        "hosts": {host["name"].split(":")[0]: None for host in hosts["items"] if "172.20." not in host["name"]}
    }
}

inventory_filename = s200.mgt_ip[:2] + "_inventory.json"

os.makedirs("ansible/inventory", exist_ok=True)
with open(f"ansible/inventory/{inventory_filename}", "w") as inv_file:
    json.dump(inventory, inv_file, indent=4)

logger.write_log(f"Inventory created: ansible/inventory/{inventory_filename}", show_output=True)

# Create final snapshots on Legacy and wait 30 seconds for them to settle #
for fs in legacy_filesystems:
    try:
        if fs["promotion_status"] == "promoted":
            legacy.post_filesystem_snapshot(fs["name"], "pre-swap")
    except ApiError as e:
        if e.code == 6:
            logger.write_log(f"Replica link doesn't exist for file system {fs['name']}. Creating non-replication snapshot.", show_output=True)
            legacy.post_filesystem_snapshot(fs["name"], "pre-swap", replicate=False)
        elif e.code == 19:
            logger.write_log(f"Snapshot named \"pre-swap\" already exists.", show_output=True)
        else:
            e.check_details(show_code=True)
            logger.write_log(f"Could not create pre-swap snapshot for filesystem {fs['name']}", show_output=True)

logger.write_log("Waiting 30 seconds for pre-swap snapshots to settle...", show_output=True)
timer.countdown(30)

# Demote / Disable each file system on Legacy (Handle exception: non-replication snapshot error, skip demotion)
for fs in legacy_filesystems:
    try:
        demote_payload = {
            "writable": False,
            "requested_promotion_state": "demoted"
        }
        legacy.patch_filesystem(fs["name"], demote_payload)
    except ApiError as err:
        err.check_details(skip_ask_to_continue=True)
        if err.code == 32:
            demote_payload = {
                "writable": False
            }
            logger.write_log(f"Unable to demote file system: {fs['name']} - Setting to unwritable instead.", show_output=True)
            legacy.patch_filesystem(fs["name"], demote_payload)
        else:
            logger.write_log(f"Other error occurred with code: {err.code}", show_output=True)

# Patch Legacy IPs to S200
for iface in legacy_interfaces:
    if iface["name"] in s200_data_iface_names:
        payload = { "address": iface["address"] }
        s200.patch_interface(iface["name"], payload)
    else:
        # Post/create interface if not exists
        if "data" in iface["services"]:
            payload = { "address": iface["address"], "services": ["data"] }
            s200.post_interface(iface["name"], payload) 

# Patch S200 IPs to Legacy
for iface in s200_interfaces:
    if iface["name"] in legacy_data_iface_names:
        payload = { "address": iface["address"] }
        legacy.patch_interface(iface["name"], payload)

# Delete replica links on Legacy
legacy_array_connections = legacy.get_array_connections()

remote_array = legacy_array_connections["remote"]["name"]

for link in legacy_replica_links:
    fs = link["local_file_system"]["name"]
    legacy.delete_filesystem_replica_link(fs, remote_array)

# Promote / Enable each file system on S200
for fs in s200_filesystems:
    if fs["name"] in s200_promo_payloads and not fs["destroyed"]:       
        s200.patch_filesystem(fs["name"], s200_promo_payloads[fs["name"]])

# Run ansible playbook with nfs client inventory and production IP variable
print("Enter root password for ansible playbook.")
subprocess.run(["ansible-playbook", "-i", f"inventory/{inventory_filename}", "-e", f"pure_ips={production_ips}", "-k", "remount-pure.yml"], cwd="ansible")

# End stopwatch for script run time
timer.end_stopwatch()
