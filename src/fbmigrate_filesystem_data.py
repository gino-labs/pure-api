#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
from fbmigrate_configs import ConfigMigrator

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

TODO / Optional
- Migrate file systems and their configurations
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

# Create API object instances of each array
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

class FileSystemMigrator:
    def __init__(self):
        self.legacy = legacy
        self.s200 = s200
        self.logger = logger
        self.watch = watch

    # Migrate file systems created and their configurations
    def migrate_filesystem_configs(self):
        legacy_filesystems = legacy.get_filesystems()
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
                s200.post_filesystem(fs["name"], payload)
            except ApiError as e:
                if e.code == 22:
                    print(e.message, end="\n\n")
                elif e.code == 6:
                    # TODO NFS Export policy doesn't exist
                    export_policy = fs["nfs"]["export_policy"]["name"]
                    pol = legacy.get_nfs_export_policies(policies=export_policy)
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
                    s200.post_nfs_export_policy(export_policy, export_payload)
                    time.sleep(2.5)
                    s200.post_filesystem(fs["name"], payload)

    
    # Migrate file system data via replication/pcopy