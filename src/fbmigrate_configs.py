#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *

'''
DONE / TEST
- Migrate/Configure Subnets/Vlans
- Migrate/Configure Snapshot Policies
- Migrate/Configure attached file system snapshot policies
- Migrate/Confiure NFS export policies
- Migrate/Configure NFS rules
- Migrate/Configure Syslog Server Connections

TODO / Optional
- Migrate/Configure Certificates/Certificate-Group
- Migrate/Configure Directory Service
- Migrate/Configure roles
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
                s200_sub_details["s200_subnames"].append(s200_subnets["name"])
                s200_sub_details["s200_prefixes"].append(s200_subnets["prefix"])
                s200_sub_details["s200_vlans"].append(s200_subnets["vlan"])
            else:
                for sub in s200_subnets:
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
            
            for sub in legacy_subnets:
                # Skip if subnet name, prefix, or vlan already exist from s200 info gathered in s200_sub_details
                if sub["name"] in s200_subnames:
                    continue
                if sub["prefix"] in s200_prefixes:
                    continue
                if sub["vlan"] in s200_vlans:
                    continue
                
                # Check services of subnet before posting
                if not set(["replication", "management", "support"]) & set(sub.get("services")):
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

    # Migrate Snapshot policies TODO
    def migrate_snapshot_polices(self):
        legacy_snapshot_polices = legacy.get_snapshot_policies()

        for pol in legacy_snapshot_polices:
            payload = {
                "name": pol["name"],
                "enabled": pol["enabled"],
                "rules": pol["rules"]
            }
            s200.post_snapshot_policy(pol["name"], payload)

    # Migrate attached policies to file systems TODO
    def migrate_attached_snapshot_policies_to_filesystems(self):
        policies = legacy.get_snapshot_policies()

        for policy in policies:
            members = legacy.get_snapshot_policy_members(policy["name"])
            for member in members:
                # Match scheduled snapshot policies from legacy to s200 file systems
                s200.post_snapshot_policy_to_filesystem(policy["name"], member["member"]["name"])

    # Migrate NFS rules
    def migrate_nfs_rules(self):
        legacy_filesystems = legacy.get_filesystems()

        for fs in legacy_filesystems:
            nfs_config = fs["nfs"]
            payload = {
                "nfs": {
                    "rules": nfs_config["rules"]
                }
            }
            s200.patch_filesystem(fs["name"], payload)
    
    # Migrate NFS export policies
    def migrate_nfs_policies(self):
        legacy_polices = legacy.get_nfs_export_policies()

        if isinstance(legacy_polices, dict):
            legacy_polices = list(legacy_polices)

        for pol in legacy_polices:
            payload = {
                "name": pol["name"],
                "enabled": pol["enabled"],
                "rules": pol["rules"]
            }
            s200.post_nfs_export_policy(pol["name"], payload)

    # Migrate syslog server configuration
    def migrate_syslog_server(self):
        legacy_syslog = legacy.get_syslog_servers()

        if isinstance(legacy_syslog, dict):
            s200.post_syslog_server(legacy_syslog["name"], legacy_syslog["uri"])
        else:
            for syslog in legacy_syslog:
                s200.post_syslog_server(syslog["name"], syslog["uri"])
            


if __name__ == "__main__":
    migrator = ConfigMigrator()

    '''
    migrator.migrate_config_subnets()
    migrator.migrate_snapshot_polices()
    migrator.migrate_attached_snapshot_policies_to_filesystems()
    migrator.migrate_nfs_rules()
    migrator.migrate_nfs_policies()
    migrator.migrate_syslog_server()

    '''