#!/usr/bin/env python3
import json
import time
from purefb_log import *
import purefb_api as pfa


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    purelog = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()
    
    promo_test = {    
        "writable": True,
        "requested_promotion_state": "promoted" 
    }
    try:
        test = s200.patch_filesystem("test", promo_test, dumpjson=True)
    except ApiError as err:
        err.log_details(show_output=True)

    watch.end_stopwatch()
