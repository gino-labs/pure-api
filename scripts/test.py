#!/usr/bin/env python3
import json
import time
from purefb_log import *
import purefb_api as pfa


if __name__ == "__main__":
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    logger = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()

    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()

    # Testing snapshots, trying to reproduce error for pre-swap snapshots during migration

    anaconda_fs = legacy.get_filesystems(filesystems="anaconda_linux_tucson", dumpjson=True)

    legacy.post_filesystem_snapshot(anaconda_fs["name"], "pre-swap")

    watch.end_stopwatch()
