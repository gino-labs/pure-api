#!/usr/bin/env python3
import json
import time
from purefb_log import *
from purefb_api import *


if __name__ == "__main__":
    rrc_site = SiteVars()
    site_vars = rrc_site.get_site_vars() 
    legacy = FlashBladeAPI(site_vars["pb1"], site_vars["pb1_mgt"], site_vars["legacy_api_token"])
    s200 = FlashBladeAPI(site_vars["pb2"], site_vars["pb2_mgt"], site_vars["s200_api_token"])

    logger = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()

    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()

    # Testing snapshots, trying to reproduce error for pre-swap snapshots during migration

    anaconda_fs = legacy.get_filesystems(filesystems="anaconda_linux_tucson", dumpjson=True)
    try:
        legacy.post_filesystem_snapshot(anaconda_fs["name"], "pre-swap")
    except ApiError as e:
        if e.code == 6:
            legacy.post_filesystem_snapshot(anaconda_fs["name"], "pre-swap", replicate=False)
        else:
            logger.write_log(f"Could not create pre-swap snapshot for filesystem {anaconda_fs['name']}")

    watch.end_stopwatch()
