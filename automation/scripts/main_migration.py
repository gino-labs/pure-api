#!/usr/bin/env python3
from purefb_api import *
from util.pure_logging import *
from scripts.fbmigrate_configs import *
from scripts.fbmigrate_object_data import *
from scripts.fbmigrate_filesystem_data import *
from scripts.fbmigrate_incremental_rsync import *

# Main
if __name__ == "__main__":
    # Start timer
    watch = Stopwatch()
    watch.start_stopwatch()

    # Migration order of operations

    # Congifuration migration operations
    cfg_migrator.migrate_certificate()
    cfg_migrator.migrate_directory_service()
    cfg_migrator.migrate_directory_service_roles()
    cfg_migrator.migrate_snapshot_polices()
    cfg_migrator.configure_replication_snapshot_policy()
    cfg_migrator.configure_replication_net()
    cfg_migrator.configure_array_connection()
    cfg_migrator.migrate_subnets()
    cfg_migrator.configure_data_interface()

    # Filesystem migration operations
    fs_migrator.replicate_filesystems()       
    fs_migrator.migrate_filesystem_configs()
    fs_migrator.migrate_attached_snapshot_policies()
    fs_migrator.pcopy_filesystems(sparse_filesystems=[]) # Add file systems to sparse list if copying larger than expected data to destination
    fs_migrator.rsync_filesystems()

    # Check rclone package is installed first
    check_rclone = subprocess.run(["rpm", "-q", "rclone"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if check_rclone.returncode != 0:
        print("Rclone rpm package is not installed. Please install with \'sudo dnf install -y rclone\'", end="\n\n")
    else:
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