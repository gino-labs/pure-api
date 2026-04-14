#!/usr/bin/env python3
from everpure import FlashBladeAPI
from everpure import EnvironmentReader
from everpure import ApiError

azfb_vars = EnvironmentReader()

gen1 = FlashBladeAPI('', '', '')
s200 = FlashBladeAPI(*azfb_vars)

# Migrate existing subnets and VLANs
def migrate_subnets():
    g1_subnets = gen1.get_subnets()
    
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

# Create data servie interface on new FlashBlade
def create_data_interface(interface_ip, interface_vlan):
    g1_interfaces = gen1.get_network_interfaces()
    
    for face in g1_interfaces:
        if face["vlan"] == interface_vlan:
            prod_interface = face
            break

    data = {
        "address": interface_ip,
        "services": ["data"],
        "type": "vip"
    }

    s200.post_network_interfaces(prod_interface["name"], json=data)
    

# Migrate existing snapshot policies
def migrate_snapshot_policies():
    g1_snapshot_polices = gen1.get_snapshot_policies()
    
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

# Create 5 minute replication poliycy

def create_5min_replication_policy():
    data = {
        "name": "replication_policy",
        "enabled": True,
        "rules": [
            {
                "every": "300000",
                "keep_for": "3600000"
            }
        ],
    }
    s200.post_policies("replication_policy", json=data)

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
