#!/usr/bin/env python3
import json
import time
from purefb_log import *
from purefb_api import *
from fbmigrate_configs import FlashBladeMigrator


if __name__ == "__main__":
    rrc_site = SiteVars()
    pb1_vars = rrc_site.get_pb1_vars()
    pb2_vars = rrc_site.get_pb2_vars()

    legacy = FlashBladeAPI(*pb1_vars)
    s200 = FlashBladeAPI(*pb2_vars)

    logger = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()

    home = s200.get_filesystems(filesystems="home_linux_tucson")

    logger.dump_config(home, "s200_home_linux_tucson")

    data = logger.load_config("s200_home_linux_tucon")

    print(data) 

    watch.end_stopwatch()
