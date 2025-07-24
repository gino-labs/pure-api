#!/usr/bin/env python3
import json
import time
import purefb_api as pfa
import pure_migration_v3 as pv3


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    snapshot_policies = legacy.get_snapshot_policies(dumpjson=False)
    
    policy_list = []
    for pol in snapshot_policies:
        policy_name = pol["policy"]["name"]
        if policy_name not in policy_list:
            policy_list.append(policy_name)

    for pol in policy_list:
        policy_info = s200.get_single_snapshot_policy(pol, dumpjson=True)