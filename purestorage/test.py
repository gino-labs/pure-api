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

    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)
    
    demote_payload = {
        "writable": False,
        "requested_promotion_state": "demoted"
    }

    promote_payload = {
        "writable": True,
        "requested_promotion_state": "promoted"
    }

    legacy.post_filesystem_snapshot("anaconda_linux_denver", "test-snap-again", dumpjson=True)
    data = legacy.patch_filesystem("testing_fail", promote_payload)

    print(data)
