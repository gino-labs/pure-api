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

    usages = s200.get_users_filesystem_usage("home_linux_tucson", dumpjson=True)

    def h_readable_size(bytes):
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(bytes)
        for unit in units:
            if size < 1024:
                return f"{size:.1f}{unit}"
        return f"{size:.1f}PB"
    
    user_filesystem_usages = [] 

    for usage in usages:
        curr_item = {
            "name": usage["name"],
            "file_system": usage["file_system"]["name"],
            "user_id": usage["user"]["id"],
            "user_name": usage["user"]["name"],
            "file_system_default_quota": usage["file_system_default_quota"],
            "usage_bytes": usage["usage"],
            "readable_usage": h_readable_size(usage["usage"])
        }
        user_filesystem_usages.append(curr_item)

    with open("logs/azhome-user-usages.json", "w") as json_f:
         json.dump(user_filesystem_usages, json_f, indent=4)

    watch.end_stopwatch()
