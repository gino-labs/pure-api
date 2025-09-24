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
    watch = pl.Stopwatch()

    watch.start_stopwatch()
    
    promo_test = {    
        "writable": True,
        "requested_promotion_state": "promoted" 
    }
    test = s200.patch_filesystem("test", promo_test, dumpjson=True)

    if "errors" in test:
        print("Errors found.")
    else:
        print("Errors not found.")

    watch.end_stopwatch()
