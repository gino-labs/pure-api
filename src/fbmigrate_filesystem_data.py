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
                # Replication not supported, append to pcopy
                if e.code == 22:
                    self.logger.write_log(f"Unable to replicate {fs['name']}. ERROR: {e.message}", show_output=True)
                else:
                    e.check_details()
                    sys.exit(1)

    # Migrate file systems created and their configurations
    def migrate_filesystem_configs(self):
        legacy_filesystems = self.legacy.get_filesystems()
        for fs in legacy_filesystems:
        
            payload = {
                "default_group_quota": fs["default_group_quota"],
                "default_user_quota": fs["default_user_quota"],
                "fast_remove_directory_enabled": fs["fast_remove_directory_enabled"], 
                "hard_limit_enabled": fs["hard_limit_enabled"], 
                "http": fs["http"], 
                "multi_protocol": fs["multi_protocol"], 
                "nfs": fs["nfs"], 
                "provisioned": fs["provisioned"], 
                "smb": fs["smb"], 
                "snapshot_directory_enabled": fs["snapshot_directory_enabled"],
                "requested_promotion_state": "demoted", 
                "writable": False, 
            }

            try:
                self.s200.post_filesystem(fs["name"], payload)
            except ApiError as e:
                if "exists" in e.message:
                    try:
                        self.s200.patch_filesystem(fs["name"], payload)
                    except ApiError:
                        pass
                e.check_details(show_code=True)
    
    # Migrate file system data via pcopy
    def pcopy_filesystems(self):

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

            pcopier.pcopy()

            pcopier.umount()

            self.refresh_api_session()
            self.legacy.patch_nfs_rule(fs["name"], f"{local_ip}(ro,no_root_squash)", remove=True)
            self.s200.patch_nfs_rule(fs["name"], f"{local_ip}(rw,no_root_squash)", remove=True)

    # Run incremental rsyncs after pcopy
    def rsync_filesystems(self):
        rsyncer = PureRsyncer()

        legacy_filesystems = [fs["name"] for fs in self.legacy.get_filesystems()]
        replication_filesystems = [link["local_file_system"]["name"] for link in self.legacy.get_bucket_replia_links()]  

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
    fs_migrator.pcopy_filesystems()
    fs_migrator.rsync_filesystems()