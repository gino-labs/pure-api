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

    s200_users = s200.get_object_store_users(dumpjson=True)

    # List of s200 object store user names
    if s200_users is not []:
        s200_user_names = [user["name"] for user in s200_users]
        print(s200_user_names)
    else:
        print("s200 users is None.")