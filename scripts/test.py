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

    gxc_bucket_link = legacy.get_bucket_replia_links(buckets="gxc-bucket")
    gxc_bucket = gxc_bucket_link["local_bucket"]["name"]

    legacy.delete_bucket_replica_link(gxc_bucket, remote_name)

    watch.end_stopwatch()
