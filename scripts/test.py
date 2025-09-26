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

    policies = legacy.get_snapshot_policies()
    for pol in policies:
        print(pol["name"])

    watch.end_stopwatch()
