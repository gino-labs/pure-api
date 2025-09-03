#!/usr/bin/env python3
import json
import time
import purefb_log as pl
import purefb_api as pfa
import pure_migration_v3 as pv3


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    purelog = pl.PureLog()

    bucket = legacy.get_buckets(buckets="gxc-bucket")
    credential = legacy.get_object_store_remote_credentials(credentials="azpureblade/gxc-remote-creds", dumpjson=True)
    s200_bucket = s200.get_buckets("gxc-bucket")

    bucket_id = bucket["id"]
    s200_bucket_id = s200_bucket["id"]

    credential_name = credential["name"]
    credential_id = credential["id"]

    payload = {
        "paused": False,
        "cascading_enabled": False
    }
    legacy.post_bucket_replica_link("gxc-bucket", credential_id, payload)

