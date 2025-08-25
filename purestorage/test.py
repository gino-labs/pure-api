#!/usr/bin/env python3
import json
import time
import purefb_log as pl
import purefb_api as pfa
import pure_migration_v3 as pv3


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    vers = legacy.get_api_version()
    vers200 = s200.get_api_version()

    purelog = pl.PureLog()
    '''
    purelog.write_log("Testing POST replica link to see replication error from older filesystems")
    filesystem = "anaconda_linux_tucson"
    payload = {
        "policies": [
            {
                "name": "5_min",
            }
        ]
    }
    purelog.write_log(f"Using {filesystem} for testing replica link post")
    fs = legacy.get_single_filesystem("anaconda_linux_tucson", dumpjson=True)
    fs_replica_link = legacy.get_single_filesytem_replica_link("anaconda_linux_tucson", dumpjson=True)
    purelog.write_log(f"Check json output of {fs}", jsondata=fs)
    purelog.write_log(f"Check json output of {fs_replica_link}", jsondata=fs_replica_link)
    #post = legacy.post_filesystem_replica_link("anaconda_linux_tucson", payload)
    '''

    s200.get_filesystems(filesystems=["anaconda_linux_tucson"], dumpjson=True)

