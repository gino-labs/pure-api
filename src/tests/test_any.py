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
    
    policy_test = s200.get_snapshot_policy_members(policies="weekly", dumpjson=True)

    mems = s200.get_endpoint("policies/members", params="policy_names=weekly&member_types=file-systems", dumpjson=True)
    for mem in mems:
        print(mem["member"]["name"])

    watch.end_stopwatch()
