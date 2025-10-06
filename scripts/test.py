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

    payload = {
        "enabled": True,
        "rules": [
            {
                "access": "no-squash",
                "client": rrc_site.get_local_ip(),
                "permission": "rw"
            },
        ]
    }

    s200.patch_nfs_export_policy("test", payload, dumpjson=True)

    watch.end_stopwatch()
