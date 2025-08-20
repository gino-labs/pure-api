#!/usr/bin/env python3
import purefb_api as pfa
import purefb_log as pfl
import subprocess
import tempfile
import time
import json
import os

logger = pfl.PureLog()

# Get auth tokens #
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

# Get List of Filesystems on Legacy #
filesystems = legacy.get_filesystems()
logger.write_log("Legacy filesystems configuration below in json format", jsondata=filesystems)

# Get list of filesystems to Promote on S200
filesystems200 = s200.get_filesystems()
logger.write_log("S200 filesystems configuration below in json format", jsondata=filesystems200)

fs200_names = []
for fs in filesystems200:
    fs200_names.append(fs["name"])
logger.write_log("S200 list of filesystem names used for comparing to legacy filesystems", jsondata=fs200_names)

# Get Interface info from legacy #
ifaces = legacy.get_interfaces()
data_iface_names = []
original_ips = [] # Orignal production IPs to check on NFS clients later #
logger.write_log("Legacy interfaces configuration below in json format", jsondata=ifaces)

for iface in ifaces:
    if "data" in iface["services"]:
        data_iface_names.append(iface["name"])
        original_ips.append(iface["address"])

if len(original_ips) > 1:
    pure_ips = "|".join(original_ips)
elif len(original_ips) == 1:
    pure_ips = original_ips[0]
else:
    print("No data interfaces.")
    print()

logger.write_log("List of legacy data interfaces names for comparison against s200", jsondata=data_iface_names)
logger.write_log(f"Original, Production IPs gathered: {pure_ips}")

# Get Interface info from s200 #
ifaces_s200 = s200.get_interfaces()
data_iface_names_s200 = []
logger.write_log("s200 interfaces configuration below in json format", jsondata=ifaces_s200)

for iface in ifaces_s200:
    if "data" in iface["services"]:
        data_iface_names_s200.append(iface["name"])

logger.write_log("List of s200 data interfaces names for comparison against legacy", jsondata=data_iface_names_s200)

# Get filesystem replica links
links = legacy.get_filesytem_replica_links()
logger.write_log("Replica links gathered on legacy", jsondata=links)

# Get NFS clients before swapping IPs #
print("Getting list of active NFS clients to the pure...")
print()
clients = legacy.get_nfs_clients()
logger.write_log("Gathered NFS clients from legacy")

hosts = []
for client in clients:
    host = client["name"]
    if "172.20.0." not in host:
        host = host.split(":")[0]
        hosts.append(host)

inventory = {
    "all": {
        "hosts": {host: None for host in hosts}
    }
}
logger.write_log("Non replication IPs/hosts in json format to make up ansible inventory", jsondata=inventory)