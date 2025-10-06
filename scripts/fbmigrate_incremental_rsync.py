#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
from purefb_subprocess import PureSubprocessor
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize objects

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

# Define rsync wrapper function for data migration
def rsync_filesystem(filesystem):
    fs_processor = PureSubprocessor(filesystem, rrc_site.get_pb1_data_ip(), rrc_site.get_pb2_data_ip())

    # Make directories for mount points
    fs_processor.mkdir()

    # Mount file systems
    fs_processor.mount()

    # Rsync file systems
    rsync_args = ["--delete", "--info=progress2", "--exclude", ".snapshot/"]
    if "home" in filesystem:
        rsync_args = rsync_args + ["--exclude", "/home/*/.cache/"]
    fs_processor.rsync()

    # Unmount file systems after done
    fs_processor.umount()

# Define file systems that need to be migrated (Non-replication)
def get_filesystems_to_rsync():
    legacy_replica_links = legacy.get_filesytem_replica_links()
    legacy_filesystems = legacy.get_filesystems()

    legacy_fs_list = [fs["name"] for fs in legacy_filesystems]
    legacy_replica_fs_list = [link["local_file_system"]["name"] for link in legacy_replica_links]

    rsync_list = set(legacy_fs_list) - set(legacy_replica_fs_list)

    return list(rsync_list)


# Main
if __name__ == "__main__":
    
    test_fs = ["anaconda_linux_tucson", "rhel6_repos_linux_tucson", "docushare-backup"]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(rsync_filesystem, fs) for fs in test_fs]
        for f in as_completed(futures):
            print(f.result())

