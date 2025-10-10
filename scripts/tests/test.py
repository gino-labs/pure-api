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

    legacy_array_connections = legacy.get_array_connections()
    remote_name = legacy_array_connections["remote"]["name"]

    credentials = legacy.get_object_store_remote_credentials()

    gxc_bucket_json = legacy.get_buckets(buckets="gxc-bucket")
    gxc_account = gxc_bucket_json["account"]["name"]

    for cred in credentials:
        if gxc_account in cred["name"]:
            remote_credential = cred["name"]
            break

    payload = {
            "paused": False,
            "cascading_enabled": False
        }

    legacy.post_bucket_replica_link("gxc-bucket", remote_credential, payload)

    watch.end_stopwatch()
