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
    
    s200.patch_interface("gxc-testing", {"address": "10.232.0.12"})

    ana = legacy.get_filesytem_replica_links(filesystems="anaconda_linux_denver")

    purelog.write_log(f"Deleting replication link for {ana['local_file_system']['name']}", show_output=True)
    test_dat = legacy.delete_filesystem_replica_link(ana["id"])

    payload = {
        "policies": [
            {
                "name": "5_min",
            }
        ]
    }

    legacy.post_filesystem_replica_link(ana["id"], payload)