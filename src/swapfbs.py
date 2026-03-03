#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
import subprocess
import json
import os

# Logger object 
logger = PureLog()

# Initialize Stopwatch object then start 
timer = Stopwatch()
timer.start_stopwatch()

# Environment variables sourced from shell (site specific)
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# FlashBlade API Object Instances 
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

# Get Legacy file systems 
legacy_filesystems = legacy.get_filesystems()

# Get S200 file systems 
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
        "writable": True,
        "requested_promotion_state": "promoted" 
    }

# Get Legacy interfaces' info 
legacy_interfaces = legacy.get_interfaces()

legacy_data_iface_names = []
legacy_data_ips = []

for iface in legacy_interfaces:
    if "data" in iface["services"] and "replication" not in iface["services"]:
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

# Get S200 interfaces' info
s200_interfaces = s200.get_interfaces()

s200_data_iface_names = [iface["name"] for iface in s200_interfaces if "data" in iface["services"]]

# Match interfaces by same subnet 
interfaces_matching_subnets = {}
for iface200 in s200_interfaces:
    if "data" in iface200["services"]:
        iface200_subnet = iface200["subnet"]["name"]
        for iface in legacy_interfaces:
            if "data" in iface["services"] and iface200_subnet == iface["subnet"]["name"]:
                interfaces_matching_subnets[iface["name"]] = iface200["name"]

# Get file system replica links on Legacy
replication_filesystems = [link["local_file_system"]["name"] for link in legacy.get_filesystem_replica_links()]

# Get bucket replica links on legacy
replication_buckets = [link["local_bucket"]["name"] for link in legacy.get_bucket_replia_links()]

# Get active NFS clients before swapping ~30 second wait
hosts = legacy.get_nfs_clients()

# Create inventory file with NFS clients obtained
inventory = {
    "all": {
        "hosts": {host["name"].split(":")[0]: None for host in hosts["items"] if "172.20." not in host["name"]} # FIXME?
    }
}

inventory_filename = s200.mgt_ip[:2] + "_inventory.json"

# TODO Evaluate inventory handling
os.makedirs("ansible/inventory", exist_ok=True)
with open(f"ansible/inventory/{inventory_filename}", "w") as inv_file:
    json.dump(inventory, inv_file, indent=4)

# Create final snapshots on Legacy and wait 30 seconds for them to settle #
for fs in legacy_filesystems:
    # TODO Evaluate error/handling
    try:
        if fs["promotion_status"] == "promoted":
            legacy.post_filesystem_snapshot(fs["name"], "pre-swap")
    except ApiError as e:
        if e.code == 6:
            legacy.post_filesystem_snapshot(fs["name"], "pre-swap", replicate=False) # Non-replication snapshot for applicable filesystems
        elif e.code == 19:
            pass # pre-swap snapshot exists
        else:
            e.check_details(show_code=True) # Error creating pre-swap snapshot

# TODO Notice of 30 second wait for snapshots
timer.countdown(30)

# Demote / Disable each file system on Legacy (Handle exception: non-replication snapshot error, skip demotion)
for fs in legacy_filesystems:
    # TODO Evaluate error/handling
    try:
        demote_payload = {
            "writable": False,
            "requested_promotion_state": "demoted"
        }
        legacy.patch_filesystem(fs["name"], demote_payload)
    except ApiError as e:
        if e.code == 32:
            demote_payload = {
                "writable": False
            }
            legacy.patch_filesystem(fs["name"], demote_payload) # Set unwritable only
        else:
            e.check_details()

# Patch/Post Legacy IPs to S200
post_ifaces = []
for iface in legacy_interfaces:
    if iface["name"] in s200_data_iface_names:
        payload = { "address": iface["address"] }
        s200.patch_interface(iface["name"], payload)
    # Use matching subnet interface info
    elif iface["name"] in interfaces_matching_subnets:
        # Patch s200 interface instead with matching subnet
        payload = { "address": iface["address"] }
        s200.patch_interface(interfaces_matching_subnets[iface["name"]], payload)
    else:
        # Post/create interface if not exists # New for AZ
        if "data" in iface["services"] and "replication" not in iface["services"]:
            # New iface name <subnet-name>-interface
            if "-subnet" in iface["subnet"]["name"]:
                new_iface_name = iface["subnet"]["name"].replace("-subnet", "-interface")
            else:
                new_iface_name = iface["subnet"]["name"] + "-interface"
            post_ifaces.append(iface)
            payload = { "address": iface["address"], "services": ["data"], "type": "vip" }
            s200.post_interface(new_iface_name, payload) 

# Patch S200 IPs to Legacy
for iface in s200_interfaces:
    payload = { "address": iface["address"] }
    if iface["name"] in legacy_data_iface_names:
        legacy.patch_interface(iface["name"], payload)
    elif iface["name"] in interfaces_matching_subnets.values():
        for key, value in interfaces_matching_subnets.items():
            if value == iface["name"]:
                legacy.patch_interface(key, payload)
        
# Delete clean up legacy ips that were posted instead of patched
for iface in post_ifaces:
    legacy.delete_interface(iface)

# Delete file system replication links on Legacy
legacy_array_connections = legacy.get_array_connections()

remote_array = legacy_array_connections["remote"]["name"]

for filesystem in replication_filesystems:
    legacy.delete_filesystem_replica_link(filesystem, remote_array)

# Delete file system replication links on Legacy
for bucket in replication_buckets:
    legacy.delete_bucket_replica_link(bucket, remote_array)

# Promote / Enable each file system on S200
for fs in s200_filesystems:
    if fs["name"] in s200_promo_payloads and not fs["destroyed"]:       
        s200.patch_filesystem(fs["name"], s200_promo_payloads[fs["name"]])

# Run ansible playbook with nfs client inventory and production IP variable
print("Enter root password for ansible playbook.")

# FIXME Hard-Coded inventory
subprocess.run(["ansible-playbook", "-i", f"inventory/az_inventory.json", "-e", f"pure_ips={production_ips}", "-k", "remount-pure.yml"], cwd="ansible")

# End stopwatch for script run time
timer.end_stopwatch()
