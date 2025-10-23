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

    usage = s200.get_users_filesystem_usage("home_linux_tucson", dumpjson=True)

    with open("logs/azhome-user-quotas.json", "w") as json_f:
         json.dump(usage, json_f, indent=4)

    watch.end_stopwatch()
