#!/usr/bin/env python3
import sys
from purefb_api import *
from purefb_log import *
from purefb_subprocess import PureSubprocessor
from fbmigrate_configs import ConfigMigrator
from fbmigrate_incremental_rsync import PureRsyncer

'''
Example payload for legacy.post_filesystem_replica_link(filesystem, remote_array, payload)

payload = {
        "policies": [
            {
                "name": "5_mins",
                "location": {
                    "name": "bazpureblade1"
                }
            }
        ]
    }


Api Error info for handling errors in script

# Post replication link errors
purefb_api.ApiError: [Code: 22] Replication is not supported for a file system that was created in a version prior to 3.0.0.

# Post file system errors
purefb_api.ApiError: [Code: 22] File system anaconda_linux_tucson already exists.

purefb_api.ApiError: [Code: 6] NFS export policy does not exist.
'''

'''
DONE / TEST
- Migrate file systems and their configurations

TODO / Optional
- Migrate file data with replication links
- Migrate file data with pcopy if replication not possible 
'''

# Logger object for logs
logger = PureLog()

# Stopwatch for script runtimes
watch = Stopwatch()

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

class FileSystemMigrator:
    def __init__(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)
        self.logger = logger
        self.watch = watch

    def refresh_api_session(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)

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
                "writable": fs["writable"], 
            }

            try:
                self.s200.post_filesystem(fs["name"], payload)
            except ApiError as e:
                if e.code == 22:
                    print(e.message, end="\n\n")
                elif e.code == 6:
                    # TODO NFS Export policy doesn't exist
                    export_policy = fs["nfs"]["export_policy"]["name"]
                    pol = self.legacy.get_nfs_export_policies(policies=export_policy)
                    rules = []
                    for rule in pol["rules"]:
                        rules.append(
                            {
                                "access": rule["access"],
                                "anongid": rule["anongid"],
                                "anonuid": rule["anonuid"],
                                "atime": rule["atime"],
                                "client": rule["client"],
                                "fileid_32bit": rule["fileid_32bit"],
                                "permission": rule["permission"],
                                "secure": rule["secure"],
                                "security": rule["security"],
                            }
                        )
                    export_payload = {
                        "name": pol["name"],
                        "enabled": pol["enabled"],
                        "rules": rules
                    }
                    self.s200.post_nfs_export_policy(export_policy, export_payload)
                    time.sleep(2.5)
                    self.s200.post_filesystem(fs["name"], payload)

    
    # Migrate file system data via replication/pcopy
    def migrate_filesystem_data(self):

        # Try replication first, needs local file system, remote array, and remote file system optional
        remote_array = self.legacy.get_array_connections()

        if isinstance(remote_array, dict):
            remote_name = remote_array["remote"]["name"]
        else:
            if len(remote_array) == 0:
                # No remote arrays found, configure one
                sys.exit("No remote arrays found. Please configure a remote array for replication. Exiting.\n")

        legacy_filesystems = self.legacy.get_filesystems()

        legacy_snapshot_polices = self.legacy.get_snapshot_policies()
        max_frequency = float("inf")
        for pol in legacy_snapshot_polices:
            if pol["rules"]:
                for rule in pol["rules"]:
                    if rule["every"] < max_frequency:
                        max_frequency = rule["every"]
                        policy_name = pol["name"]
                        location_name = pol["location"]["name"]

        logger.write_log("Trying to create replication links, then falling back to pcopy if not supported.", show_output=True)
        pcopy_filesystem_list = []
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
                    print(e.message)
                    logger.write_log(f"Adding {fs['name']} to list of filesystems to pcopy", show_output=True)
                    pcopy_filesystem_list.append(fs)

        # Pcopy file systems with no replication support
        if len(pcopy_filesystem_list) > 0:
            for fs in pcopy_filesystem_list:
                self.refresh_api_session()
                
                pcopier = PureSubprocessor(fs["name"], rrc_site.get_pb1_data_host(), rrc_site.get_pb2_data_host())
                
                local_ip = rrc_site.get_local_ip()
                if f"{local_ip}(ro,no_root_squash)" not in fs["nfs"]["rules"]:
                    self.legacy.patch_nfs_rule(fs["name"], f"{local_ip}(ro,no_root_squash)")
                    self.s200.patch_nfs_rule(fs["name"], f"{local_ip}(rw,no_root_squash)")
                
                pcopier.mkdir()

                pcopier.mount()

                pcopier.pcopy()

                pcopier.umount()

                self.legacy.patch_nfs_rule(fs["name"], f"{local_ip}(ro,no_root_squash)", remove=True)
                self.s200.patch_nfs_rule(fs["name"], f"{local_ip}(rw,no_root_squash)", remove=True)

            # Run incremental rsyncs after pcopy
            rsyncer = PureRsyncer()

            rsyncer.run_incremental_rsyncs(fs_list=pcopy_filesystem_list)




                    
            
        
                    
