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
    filesystems = legacy.get_filesystems()
    print(f"Length of filesystems: {len(filesystems)}")
    print()

    replica_links = legacy.get_filesytem_replica_links()
    print(f"Length of replica links: {len(replica_links)}")
    print()
    
    fs_names = [fs["name"] for fs in filesystems]

    for link in replica_links:
        if link["local_file_system"]["name"] not in fs_names:
            print(link["local_file_system"]["name"])
        else:
            print(f"{link['local_file_system']['name']} is in list.")

    print(json.dumps(fs_names, indent=4))
    watch.end_stopwatch()
