#!/usr/bin/env python3
import sys
from purefb_api import *
from purefb_log import *
from purefb_subprocess import PureSubprocessor
from fbmigrate_incremental_rsync import PureRsyncer

'''
# Post replication link errors
purefb_api.ApiError: [Code: 22] Replication is not supported for a file system that was created in a version prior to 3.0.0.

# Post file system errors
purefb_api.ApiError: [Code: 22] File system anaconda_linux_tucson already exists.
purefb_api.ApiError: [Code: 6] NFS export policy does not exist.
'''

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

class FileSystemMigrator:
    def __init__(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)
        self.logger = PureLog()
        self.watch = Stopwatch()

    def refresh_api_session(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)

    # Try to establish replication links
    def replicate_filesystems(self):
        remote_array = self.legacy.get_array_connections()

        if isinstance(remote_array, list):
            remote_array = remote_array[0]
        
        remote_name = remote_array["remote"]["name"]

        legacy_filesystems = self.legacy.get_filesystems()

        legacy_pol = self.legacy.get_snapshot_policies(policies="5_mins")
        
        policy_name = legacy_pol["name"]
        location_name = legacy_pol["location"]["name"]

        self.logger.write_log("Trying to create replication links", show_output=True)
        for fs in legacy_filesystems():
            # Try replication link
            try:
                payload = {
                    "policies": [
                        {
                            "name": policy_name,
                            "location": {
                                "name": location_name
                            }
                        }
                    ]
                }
                self.legacy.post_filesystem_replica_link(fs["name"], remote_name, payload)
            except ApiError as e: 
                # Replication not supported
                if e.code == 22:
                    self.logger.write_log(f"Unable to replicate {fs['name']}. ERROR: {e.message}", show_output=True)
                else:
                    e.check_details()

    # Migrate file systems created and their configurations
    def migrate_filesystem_configs(self):
        legacy_filesystems = self.legacy.get_filesystems()
        s200_filesystems = [fs["name"] for fs in self.s200.get_filesystems()]
        replication_filesystems = [link["local_file_system"]["name"] for link in self.legacy.get_filesytem_replica_links()]  
         
        for fs in legacy_filesystems:
            try:
                if fs["nfs"]["export_policy"]["name"]:
                    nfs = { "v3_enabled": fs["nfs"]["v3_enabled"], "v4_1_enabled": fs["nfs"]["v4_1_enabled"], "export_policy": {"name": fs["nfs"]["export_policy"]["name"]} }
                else:
                    nfs = { "v3_enabled": fs["nfs"]["v3_enabled"], "v4_1_enabled": fs["nfs"]["v4_1_enabled"], "rules": fs["nfs"]["rules"] }
                
                if fs in replication_filesystems:
                    writable = False
                else:
                    writable = True

                payload = {
                    "default_group_quota": fs["default_group_quota"],
                    "default_user_quota": fs["default_user_quota"],
                    "fast_remove_directory_enabled": fs["fast_remove_directory_enabled"], 
                    "hard_limit_enabled": fs["hard_limit_enabled"], 
                    "http": fs["http"], 
                    "multi_protocol": fs["multi_protocol"], 
                    "nfs": nfs, 
                    "provisioned": fs["provisioned"], 
                    "snapshot_directory_enabled": fs["snapshot_directory_enabled"],
                    "writable": writable, 
                }               

                if fs["name"] in s200_filesystems:
                    self.s200.patch_filesystem(fs["name"], payload)
                else: 
                    self.s200.post_filesystem(fs["name"], payload)
            except ApiError as e:
                e.check_details()

    # Migrate attached policies to file systems
    def migrate_attached_snapshot_policies(self):
        policies = self.legacy.get_snapshot_policies()
        if isinstance(policies, dict):
            policies = [policies]

        for policy in policies:
            members = self.legacy.get_snapshot_policy_members(policy["name"])
            s200_members = [member["member"]["name"] for member in self.s200.get_snapshot_policy_members(policy["name"])]

            if isinstance(members, dict):
                members = [members]

            if isinstance(s200_members, dict):
                s200_members = [s200_members]

            for member in members:
                # Match scheduled snapshot policies from legacy to s200 file systems
                if member["member"]["name"] in s200_members:
                    self.logger.write_log(f"Filesystem {member['member']['name']} already attach with {policy['name']}", show_output=True)
                else:
                    try: 
                        self.s200.post_snapshot_policy_to_filesystem(policy["name"], member["member"]["name"])
                    except ApiError as e:
                        e.check_details()

    # Migrate file system data via pcopy
    def pcopy_filesystems(self, sparse_filesystems=[]):

        legacy_filesystems = [fs["name"] for fs in self.legacy.get_filesystems()]
        replication_filesystems = [link["local_file_system"]["name"] for link in self.legacy.get_filesytem_replica_links()]  

        # list of non replication file systems
        pcopy_list = list(set(legacy_filesystems) - set(replication_filesystems))

        # Process each filesystem and add rules if necessary
        for fs in pcopy_list:
            pcopier = PureSubprocessor(fs["name"], rrc_site.get_pb1_data_host(), rrc_site.get_pb2_data_host())
            
            local_ip = rrc_site.get_local_ip()
            if f"{local_ip}(ro,no_root_squash)" not in fs["nfs"]["rules"]:
                self.legacy.patch_nfs_rule(fs["name"], f"{local_ip}(ro,no_root_squash)")
                self.s200.patch_nfs_rule(fs["name"], f"{local_ip}(rw,no_root_squash)")
            
            pcopier.mkdir()

            pcopier.mount()
            
            if fs["name"] in sparse_filesystems:
                pcopier.pcopy(extra_args=["--sparse=always"])
            else:
                pcopier.pcopy()

            pcopier.umount()

            self.refresh_api_session()
            self.legacy.patch_nfs_rule(fs["name"], f"{local_ip}(ro,no_root_squash)", remove=True)
            self.s200.patch_nfs_rule(fs["name"], f"{local_ip}(rw,no_root_squash)", remove=True)

    # Run incremental rsyncs after pcopy
    def rsync_filesystems(self):
        rsyncer = PureRsyncer()

        legacy_filesystems = [fs["name"] for fs in self.legacy.get_filesystems()]
        replication_filesystems = [link["local_file_system"]["name"] for link in self.legacy.get_filesystem_replica_links()]  

        # list of non replication file systems
        rsync_list = list(set(legacy_filesystems) - set(replication_filesystems))

        rsyncer.run_incremental_rsyncs(fs_list=rsync_list)


# Main
if __name__ == "__main__":
    # Filesystem Migrator Instance
    fs_migrator = FileSystemMigrator()

    # Filesystem migration operations in the following order
    fs_migrator.replicate_filesystems()       
    fs_migrator.migrate_filesystem_configs()
    fs_migrator.migrate_attached_snapshot_policies()
    fs_migrator.pcopy_filesystems(sparse_filesystems=[]) # Add file systems to sparse list if copying larger than expected data to destination
    fs_migrator.rsync_filesystems()