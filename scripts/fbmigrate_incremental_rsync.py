#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
from purefb_subprocess import PureSubprocessor

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



