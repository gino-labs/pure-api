#!/usr/bin/env python3
from purefb_api import *
from util.logging import *
from util.subprocessor import PureSubprocessor
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize objects

# Logger object for logs
logger = PureLog()
summary_logger = PureLog()
summary_logger.set_logfile("rsync-summary", no_date=True)

# Stopwatch for summary log
summary_stopwatch = Stopwatch()
summary_stopwatch.set_log(summary_logger)

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

class PureRsyncer:

    def __init__(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)
        self.fs_logger = PureLog()
        self.fs_watch = Stopwatch()

    def refresh_api_sessions(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)

    # Define rsync wrapper function for data migration
    def rsync_filesystem(self, filesystem):
        
        # Set Logger Data
        self.fs_logger.set_logdir(f"{filesystem}-logs")
        self.fs_logger.set_logfile(f"{filesystem}-scriptlog")

        # Set Stopwatch Log
        self.fs_watch.set_log(self.fs_logger)

        # Start timer
        self.fs_watch.start_stopwatch(show_start_time=False)
        summary_stopwatch.start_stopwatch(show_start_time=False)

        # Patch local IP to file system NFS rules
        local_ip = rrc_site.get_local_ip()
        legacy_rule = f"{local_ip}(ro,no_root_squash)"
        s200_rule = f"{local_ip}(rw,no_root_squash)"
        self.legacy.patch_nfs_rule(filesystem, legacy_rule)
        self.s200.patch_nfs_rule(filesystem, s200_rule)

        # Initial file system processor class
        fs_processor = PureSubprocessor(filesystem, rrc_site.get_pb1_data_host(), rrc_site.get_pb2_data_host())

        # Make directories for mount points
        fs_processor.mkdir()
        self.fs_logger.write_log("Directories created for mountpoints and migration")

        # Mount file systems
        fs_processor.mount()
        self.fs_logger.write_log("File systems mounted.")

        # Rsync file systems
        self.fs_logger.write_log(f"Beginning rsync of file system {filesystem} from legacy to s200")
        rsync_args = ["--delete", "--stats","--log-file", f"{self.fs_logger.get_logdir_path()}/{filesystem}-rsync.log", "--exclude", ".snapshot/", "--exclude", ".fast-remove/"]
        if "home" in filesystem:
            rsync_args = rsync_args + ["--exclude", "*/.cache/"]
        result = fs_processor.rsync(extra_args=rsync_args)

        # Write rsync log complete
        self.fs_logger.write_log(f"File system rsync process complete with EXIT CODE: {result.returncode}")

        # Unmount file systems after done
        fs_processor.umount()
        self.fs_logger.write_log("file systems unmounted.")

        # Stop timer
        self.fs_watch.end_stopwatch(showtime=False)
        self.fs_watch.show_time_elapsed(show_output=False)

        summary_stopwatch.end_stopwatch(showtime=False)
        elapsed_time = summary_stopwatch.get_time_elapsed(time_string=True)

        summary_logger.write_log(f"File system ({filesystem}) completed rsync. {elapsed_time}")

        # Refresh new API sessions
        self.refresh_api_sessions()

        self.legacy.patch_nfs_rule(filesystem, legacy_rule, remove=True)
        self.s200.patch_nfs_rule(filesystem, s200_rule, remove=True)

        return f"File system {filesystem} has finished rsyncing. See logs at {self.fs_logger.get_logfile_path()}"

    # Define file systems that need to be migrated (Non-replication)
    def get_filesystems_to_rsync(self):

        legacy_replica_links = self.legacy.get_filesystem_replica_links()
        legacy_filesystems = self.legacy.get_filesystems()

        legacy_fs_list = [fs["name"] for fs in legacy_filesystems]
        legacy_replica_fs_list = [link["local_file_system"]["name"] for link in legacy_replica_links]

        rsync_list = set(legacy_fs_list) - set(legacy_replica_fs_list)

        return list(rsync_list)
    
    # Def run concurrent incremental rsyncs
    def run_incremental_rsyncs(self, fs_list=None):
        if fs_list is not None:
            filesystems = list(fs_list)
        else:
            filesystems = self.get_filesystems_to_rsync()

        runtime_watch = Stopwatch()
        runtime_watch.set_log(summary_logger)

        runtime_watch.start_stopwatch(show_start_time=False)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.rsync_filesystem, fs) for fs in filesystems]
            for f in as_completed(futures):
                try:
                    logger.write_log(f.result(), show_output=True)
                except Exception as e:
                    logger.write_log(f"Exception has occurred: {e}", show_output=True)

        runtime_watch.end_stopwatch(showtime=False)

        runtime = runtime_watch.get_time_elapsed(time_string=True)
        summary_logger.write_log(f"All filesystesms rsynced. {runtime}\n---", show_output=True)

# Main
if __name__ == "__main__":
    # Class instances
    rsyncer = PureRsyncer()
    legacy = FlashBladeAPI(*pb1_vars)

    # File systems
    legacy_filesystems = [fs["name"] for fs in legacy.get_filesystems()]
    replication_filesystems = [link["local_file_system"]["name"] for link in legacy.get_filesystem_replica_links()]  

    # list of non replication file systems
    rsync_list = list(set(legacy_filesystems) - set(replication_filesystems))

    # Run rsyncs
    rsyncer.run_incremental_rsyncs(fs_list=rsync_list)

