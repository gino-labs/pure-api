#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
import subprocess
import json
import os

# Logger object
scriptlog = PureLog()

# Initialize Stopwatch object then start
timer = Stopwatch()
timer.start_stopwatch()

# FlashBlade API Object Instances
# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# Create API object instances of each array
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

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

scriptlog.write_log("Legacy data interface names list", jsondata=legacy_data_iface_names, show_output=True)
scriptlog.write_log(f"Legacy production IP list and ansible var {production_ips}", jsondata=legacy_data_ips, show_output=True)

# Get S200 interfaces' info
s200_interfaces = s200.get_interfaces()

s200_data_iface_names = [iface["name"] for iface in s200_interfaces if "data" in iface["services"]]
scriptlog.write_log("S200 data interface names list", jsondata=s200_data_iface_names, show_output=True)

# Match interfaces by same subnet
interfaces_matching_subnets = {}
for iface200 in s200_interfaces:
    if "data" in iface200["services"]:
        iface200_subnet = iface200["subnet"]["name"]
        for iface in legacy_interfaces:
            if "data" in iface["services"] and iface200_subnet == iface["subnet"]["name"]:
                interfaces_matching_subnets[iface["name"]] = iface200["name"]

scriptlog.write_log("Interfaces that are using the same subnets.", jsondata=interfaces_matching_subnets, show_output=True)

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

os.makedirs("ansible/inventory", exist_ok=True)
with open(f"ansible/inventory/{inventory_filename}", "w") as inv_file:
    json.dump(inventory, inv_file, indent=4)

scriptlog.write_log(f"Inventory created with name ansible/inventory/{inventory_filename}", jsondata=inventory, show_output=True)

# File systems that would be snapshotted
promoted_fs_list = []
for fs in legacy_filesystems:
    if fs["promotion_status"] == "promoted":
        promoted_fs_list.append(fs["name"])

scriptlog.write_log(f"File systems that would get pre-swap snapshot: {len(promoted_fs_list)}", jsondata=promoted_fs_list, show_output=True)

scriptlog.write_log("Waiting 30 (simulated) seconds for pre-swap snapshots to settle...", show_output=True)
timer.countdown(3)

# File systems that would be demoted or not demoted
demo_fs_list = [fs["name"] for fs in legacy_filesystems if fs["name"] in replication_filesystems]
non_demo_fs_list = [fs["name"] for fs in legacy_filesystems if fs["name"] not in replication_filesystems]
scriptlog.write_log(f"File systems that would be demoted: {len(demo_fs_list)}", jsondata=demo_fs_list, show_output=True)
scriptlog.write_log(f"File systems that would NOT be demoted because no replication snapshots: {len(non_demo_fs_list)}", jsondata=non_demo_fs_list, show_output=True)

# IPs that would be patched/posted to s200
s200_iface_json = { "patched": [], "posted": [] }

for iface in legacy_interfaces:
    # Patch
    if iface["name"] in s200_data_iface_names:
        s200_iface_json["patched"].append({iface["name"]: {"address": iface["address"]}})
    else:
        # Post data interfaces
        if "data" in iface["services"]:
            # New iface name <subnet-name>-interface
            if "-subnet" in iface["subnet"]["name"]:
                new_iface_name = iface["subnet"]["name"].replace("-subnet", "-interface")
            else:
                new_iface_name = iface["subnet"]["name"] + "-interface"
            s200_iface_json["posted"].append({new_iface_name: {"address": iface["address"], "services": ["data"]}})

s200_ifaces_updated = { "S200_Updated_Interfaces": s200_iface_json }

scriptlog.write_log(f"S200 to Legacy interfaces patched: {len(s200_iface_json['patched'])}, posted: {len(s200_iface_json['posted'])}", jsondata=s200_iface_json, show_output=True)

# IPs that would be patched to legacy
legacy_iface_json_list = []
for iface in s200_interfaces:
    if iface["name"] in legacy_data_iface_names:
        legacy_iface_json_list.append({iface["name"]: {"address": iface["address"]}})

legacy_ifaces_updated = { "Legacy_Updated_Interfaces": legacy_iface_json_list }

scriptlog.write_log(f"Legacy interfaces to be updated with S200 IPs: {len(legacy_iface_json_list)}", jsondata=legacy_ifaces_updated, show_output=True)

exit()
# Replication links that would be deleted
legacy_array_connections = legacy.get_array_connections()

remote_array = legacy_array_connections["remote"]["name"]

fs_del_replica_list = []
for link in legacy_replica_links:
    fs = link["local_file_system"]["name"]
    tmp_dict = {
        "remote_array": remote_array,
        "local_file_system": fs
    }
    fs_del_replica_list.append(tmp_dict)

scriptlog.write_log(f"Legacy file system replica links that would be deleted: {len(fs_del_replica_list)}", jsondata=fs_del_replica_list, show_output=True)

# File systems that would be promoted on S200
fs_promotions = {"promotion_due": [], "destroyed": []}
for fs in s200_filesystems:
    if fs["name"] in s200_promo_payloads and fs["destroyed"] != True:       
        fs_promotions["promotion_due"].append({fs["name"]: s200_promo_payloads[fs["name"]]})
    if fs["destroyed"]:
        fs_promotions["destroyed"].append(fs["name"])

scriptlog.write_log(f"File systems that would be promoted: {len(fs_promotions['promotion_due'])}, or not if destroyed: {len(fs_promotions['destroyed'])}", jsondata=fs_promotions, show_output=True)

# Test ansible play connectivity to nfs client inventory
print("Enter root password for ansible playbook.")
subprocess.run(["ansible-playbook", "-i", f"inventory/{inventory_filename}", "-e", f"pure_ips={production_ips}", "-k", "test-clients.yml"], cwd="ansible")

timer.end_stopwatch()
        