#!/usr/bin/env python3
import json
import time
from purefb_log import *
from purefb_api import *
from fbmigrate_configs import ConfigMigrator


if __name__ == "__main__":
    rrc_site = SiteVars()
    pb1_vars = rrc_site.get_pb1_vars()
    pb2_vars = rrc_site.get_pb2_vars()

    legacy = FlashBladeAPI(*pb1_vars)
    s200 = FlashBladeAPI(*pb2_vars)

    logger = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()

    anacon = "anaconda_linux_tucson"
    
    fs = s200.get_filesystems(filesystems=anacon)
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
    legacy.post_filesystem("gxc_" + anacon , payload)

watch.end_stopwatch()
