#!/usr/bin/env python3
import json
import time
import purefb_api as pfa
import pure_migration_v3 as pv3


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    test = legacy.get_snapshot_policies(dumpjson=True)
    
    policies = []
    for t in test:
        if t["policy"]["name"] not in policies:
            policies.append({t["policy"]["name"]: []})
        print(t["policy"]["name"])