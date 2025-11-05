#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
from fbmigrate_configs import *
from fbmigrate_object_data import *
from fbmigrate_filesystem_data import *
from fbmigrate_incremental_rsync import *

# Main
if __name__ == "__main__":
    # Start timer
    watch = Stopwatch()
    watch.start_stopwatch()

    # Migration order of operations

    # Congifuration migration operations
    cfg_migrator = ConfigMigrator()
    cfg_migrator.migrate_config_subnets()
    cfg_migrator.migrate_snapshot_polices()
    cfg_migrator.migrate_attached_snapshot_policies_to_filesystems()
    cfg_migrator.configure_replication_snapshot_policy()
    cfg_migrator.create_replication_net()
    cfg_migrator.migrate_config_array_connection()
    cfg_migrator.migrate_certificate()
    cfg_migrator.migrate_directory_service()
    cfg_migrator.migrate_directory_service_roles()
    cfg_migrator.configure_data_interface()

    # Filesystem migration operations
    fs_migrator = FileSystemMigrator()
    fs_migrator.replicate_filesystems()       
    fs_migrator.migrate_filesystem_configs()
    fs_migrator.pcopy_filesystems()
    fs_migrator.rsync_filesystems()

    # Run incremental rsyncs
    rsyncer = PureRsyncer()
    rsyncer.run_incremental_rsyncs()

    # Object migration operations
    obj_migrator = ObjectMigrator()
    obj_migrator.delete_legacy_object_replica_links()
    obj_migrator.delete_s200_access_keys()
    obj_migrator.migrate_object_store_accounts()
    obj_migrator.migrate_buckets()
    obj_migrator.migrate_object_store_users()
    obj_migrator.create_new_s200_access_keys()
    obj_migrator.create_migration_legacy_users_and_keys()
    obj_migrator.rclone_object_storage_buckets()
    obj_migrator.remove_temporary_migration_users()
    obj_migrator.add_remote_credentials()
    obj_migrator.create_bucket_replica_links()

    # End timer
    watch.end_stopwatch()