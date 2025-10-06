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

    test_pol = s200.get_nfs_export_policies(policies="test", dumpjson=True)
    rules = test_pol["rules"]
    for rule in rules:
        del rule["name"]
        del rule["id"]
        del rule["policy"]
        del rule["index"]
        del rule["policy_version"]
    new_rules = [rule for rule in rules]
    
    new_rule = {
        "rules": [

            {
                "access": "no-squash",
                "client": "172.16.203.133",
                "permission": "rw"
            },
        ]
    }
    new_rules.append(new_rule)
    
    payload = { 
        "rules": new_rules
    }


    s200.patch_nfs_export_policy("test", payload, dumpjson=True)

    watch.end_stopwatch()
