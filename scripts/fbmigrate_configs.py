#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *


'''
TODO
- Migrate/Configure Subnets/Vlans # Test
- Migrate/Configure DNS
- Migrate/Configure NTP
- Migrate/Configure Policies
- Migrate/Configure Directory Service
- Migrate/Configure Certificates/Certificate-Group
- Migrate/Configure Syslog Server Connections
- Migrate/Configure Interfaces (Data/Replcation, ensure no duplicate IPs between blades)
'''
# Logger object for logs
logger = PureLog()

# Stopwatch for script runtimes
watch = Stopwatch()

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# Create API object instances of each array
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

class ConfigMigrator:
    def __init__(self):
        self.legacy = legacy
        self.s200 = s200
        self.logger = logger
        self.watch = watch
    
    # Migrate subnets, verify name, vlan, subnet prefix
    def migrate_config_subnets(self):
        legacy_subnets = self.legacy.get_subnets()
        s200_subnets = self.s200.get_subnets()

        # Store existing S200 subnet details to not recreate overlapping
        s200_sub_details = {
            "s200_subnames": [],
            "s200_prefixes": [],
            "s200_vlans": []
        }   
        if s200_subnets:
            if isinstance(s200_subnets, dict):
                if "data" in s200_sub_details.get(s200_subnets["services"]):
                    s200_sub_details["s200_subnames"].append(s200_subnets["name"])
                    s200_sub_details["s200_prefixes"].append(s200_subnets["prefix"])
                    s200_sub_details["s200_vlans"].append(s200_subnets["vlan"])
            else:
                for sub in s200_subnets:
                    if "data" in sub.get("services", []):
                        s200_sub_details["s200_subnames"].append(sub["name"])
                        s200_sub_details["s200_prefixes"].append(sub["prefix"])
                        s200_sub_details["s200_vlans"].append(sub["vlan"])

        # For each subnet on legacy post subnet to s200
        if legacy_subnets:
            if isinstance(legacy_subnets, dict):
                legacy_subnets = [legacy_subnets]
            s200_subnames = s200_sub_details["s200_subnames"]
            s200_prefixes = s200_sub_details["s200_prefixes"]
            s200_vlans = s200_sub_details["s200_vlans"]
            print(s200_subnames)
            print(s200_prefixes)
            print(s200_vlans)
            exit()
            for sub in legacy_subnets:
                # Skip if subnet name, prefix, or vlan already exist from s200 info gathered in s200_sub_details
                if sub["name"] in s200_subnames:
                    continue
                if sub["prefix"] in s200_prefixes:
                    continue
                if sub["vlan"] in s200_vlans:
                    continue

                payload = {
                    "gateway": sub["gateway"],
                    "link_aggregation_group": {
                        "name": sub["link_aggregation_group"]["name"]
                    },
                    "mtu": sub["mtu"],
                    "prefix": sub["prefix"],
                    "vlan": sub["vlan"]
                }
                # Post subnets to s200
                try:
                    self.s200.post_subnet(sub["name"], payload)
                except ApiError as e:
                    e.check_details(show_code=True, show_context=True)
                    print(payload["link_aggregation_group"])
                    exit()


