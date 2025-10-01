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

    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()
    
    anaconda_fs = s200.get_filesystems(filesystems="anaconda_linux_tucson", dumpjson=True)
    pascal_fs = s200.get_filesystems(filesystems="pascal_linux_tucson", dumpjson=True)

    watch.end_stopwatch()
