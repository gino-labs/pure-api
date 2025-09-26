#!/usr/bin/env python3
import json
import time
from purefb_log import *
import purefb_api as pfa


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    logger = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()

    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()

    # Create promotion payloads using corresponding legacy file system
    s200_promo_payloads = {}
    for fs in legacy_filesystems:
        s200_promo_payloads[fs["name"]] = {
            "nfs": {
                "v3_enabled": fs["nfs"]["v3_enabled"],
                "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
                "rules": fs["nfs"]["rules"]
            },
            "http": {
                "enabled": fs["http"]["enabled"]
            },
            "writable": True,
            "requested_promotion_state": "promoted" 
        }

    logger.write_log("S200 file system promotion data from legacy", jsondata=s200_promo_payloads)

    count = 0
    destroyed_found = []
    for fs in s200_filesystems:
        count += 1
        if fs["name"] in s200_promo_payloads and not fs["destroyed"]:       
            logger.write_log(f"Filesystem {fs['name']} would be promoted: {count}", jsondata=s200_promo_payloads[fs["name"]], show_output=True)
        if fs["destroyed"]:
            destroyed_found.append(fs["name"])

    logger.write_log("The following filesystems will not be promoted because they are destroyed:", jsondata=destroyed_found)
    print(f"Non destroyed filesystem count: {count}")

    watch.end_stopwatch()
