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
    # Logger Instance
    fs_logger =  PureLog()
    fs_logger.set_logfile(f"{filesystem}-rsync")

    # Stopwatch Instance
    watch = Stopwatch()
    watch.set_log(fs_logger)

    # Start timer
    watch.start_stopwatch(show_start_time=False)

    # Patch local IP to file system NFS rules
    local_ip = rrc_site.get_local_ip()
    legacy_rule = f"{local_ip}(ro,no_root_squash)"
    s200_rule = f"{local_ip}(rw,no_root_squash)"
    legacy.patch_nfs_rule(filesystem, legacy_rule)
    s200.patch_nfs_rule(filesystem, s200_rule)

    # Initial file system processor class
    fs_processor = PureSubprocessor(filesystem, rrc_site.get_pb1_data_ip(), rrc_site.get_pb2_data_ip())

    # Make directories for mount points
    fs_processor.mkdir()
    fs_logger.write_log("Directories created for mountpoints and migration")

    # Mount file systems
    fs_processor.mount()
    fs_logger.write_log("File systems mounted.")

    # Rsync file systems
    fs_logger.write_log(f"Beginning rsync of file system {filesystem} from legacy to s200")
    rsync_args = ["--delete", "--info=progress2", "--exclude", ".snapshot/"]
    if "home" in filesystem:
        rsync_args = rsync_args + ["--exclude", "/home/*/.cache/"]
    result = fs_processor.rsync()

    # Write rsync log complete
    fs_logger.write_log(f"File system rsync process complete with EXIT CODE: {result.returncode}")

    # Unmount file systems after done
    fs_processor.umount()
    fs_logger.write_log("file systems unmounted.")

    # Stop timer
    watch.end_stopwatch(showtime=False)
    watch.show_time_elapsed(show_output=False)

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
    
    filesystems = get_filesystems_to_rsync()

    print(filesystems)

    # with ThreadPoolExecutor(max_workers=3) as executor:
    #     futures = [executor.submit(rsync_filesystem, fs) for fs in test_fs]
    #     for f in as_completed(futures):
    #         print(f.result())

