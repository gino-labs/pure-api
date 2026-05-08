#!/usr/bin/env python3
from everpure import FlashBladeAPI
from everpure import PureEnvironment
from everpure import ApiError
from everpure import PureLogger

import os 

logger = PureLogger("migration")

# Source additional env variables
gen1_mgt_ip = os.environ["GEN1_MGT_IP"]
gen1_rep_ip = os.environ["GEN1_REP_IP"]
s200_mgt_ip = os.environ["S200_MGT_IP"]
s200_rep_ip = os.environ["S200_REP_IP"]
gen1_env = PureEnvironment('', '', '', mgt_ip=gen1_mgt_ip, rep_ip=gen1_rep_ip)
s200_env = PureEnvironment('', '', '', mgt_ip=s200_mgt_ip, rep_ip=s200_rep_ip)

gen1 = FlashBladeAPI('','','')
s200 = FlashBladeAPI('','','')

# Migrate existing subnets and VLANs
def migrate_subnets():
    g1_subnets = gen1.get_subnets()
    gen1.log("Get success - subnets")
    
    for sub in g1_subnets:
        data = {
            "gateway": sub["gateway"],
            "link_aggregation_groups": {
                "name": sub["link_aggregation_groups"]["name"],
            },
            "mtu": sub["mtu"],
            "prefix": sub["prefix"],
            "vlan": sub["vlan"]
        }
        s200.post_subnets(names=sub["name"], json=data)
        s200.log(f"Post success - subnet {sub['name']}")

# Create data interface on S200
def create_data_interface(interface_ip, interface_vlan):
    g1_interfaces = gen1.get_network_interfaces()
    gen1.log("Get success - network interfaces")
    
    prod_interface = None
    for iface in g1_interfaces:
        if iface["vlan"] == interface_vlan:
            prod_interface = iface
            break
    
    if prod_interface is not None:
        data = {
            "address": interface_ip,
            "services": ["data"],
            "type": "vip"
        }

        s200.post_network_interfaces(prod_interface["name"], json=data)
        s200.log(f"Post success network interface - {interface_ip} - VLAN {interface_vlan}")
    else:
        s200.log(f"NO matching VLAN {interface_vlan}")
        s200.log(f"Post skip network interface with {interface_ip}")

# Create replication subnet on Gen1 and S200
def create_replication_subnets():
    pass

# Create replication interface on Gen1 and S200
def create_replication_interfaces():
    pass

# Migrate existing snapshot policies
def migrate_snapshot_policies():
    g1_snapshot_polices = gen1.get_snapshot_policies()
    gen1.log("Get success - snapshot policies")
    
    for pol in g1_snapshot_polices:
        data = {
            "name": pol["name"],
            "enabled": pol["enabled"],
            "rules": [
                {
                    "at": pol["rules"][0]["at"],
                    "every": pol["rules"][0]["every"],
                    "keep_for": pol["rules"][0]["keep_for"],
                    "time_zone": pol["rules"][0]["time_zone"]
                }
            ]
        }
        s200.post_policies(pol["name"], json=data)
        s200.log(f"Post success - snapshot policy {pol['name']}")

# Create 5 minute replication poliycy
def create_5min_replication_policy():
    policy_name = "replication_policy"
    data = {
        "name": policy_name,
        "enabled": True,
        "rules": [
            {
                "every": "300000",
                "keep_for": "3600000"
            }
        ],
    }
    s200.post_policies(policy_name, json=data)
    s200.log(f"Post success - snapshot policy {policy_name}")

# Create Remote Array Connection / Key
def create_remote_array_connection():
    remote_arrays = s200.get_array_connections()
    s200.log("Get success - array connections")
    
    if remote_arrays == []:
        return
    
    key = s200.post_connection_key()[0]["connection_key"]
    s200.log(f"Post success - connection key {key}")
    with open(".secrets", "a") as f:
        f.write(f"\nS200 Key: {key}\n")

    

# Create file system replication links and use 5 min policy (If possible)
def create_replication_links():
    g1_filesystems = gen1.get_filesystems()
    data = {
        "policies": [
            {
                "name": "replication_policy",
                "location": {
                    "name": gen1.name
                }
            }
        ]
    }
    for fs in g1_filesystems:
        try:
            gen1.post_filesystem_replica_links(fs["name"], s200.name, json=data)
        except ApiError as e:
            print()
            print(f"Error creating replica link for {fs['name']}\nERR_MSG: {e.err_message}", end="\n\n")

# Migrate syslog server configuration

# Migrate directory services configuration

# Migrate user role mappings

# Migrate object store accounts

# Migrate object store users

# Migrate object store buckets

# Create new object store access keys

# Create bucket replication links
