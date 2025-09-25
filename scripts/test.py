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

    legacy_filesystems = [legacy.get_filesystems(filesystems="test")]
    
    for fs in legacy_filesystems:
        try:
            demote_payload = {
                "writable": False,
                "requested_promotion_state": "demoted"
            }
            legacy.patch_filesystem(fs["name"], demote_payload)
        except ApiError as err:
            err.check_details(skip_ask_to_continue=True)
            if err.code == 32:
                demote_payload = {
                    "writable": False
                }
                legacy.patch_filesystem(fs["name"], demote_payload)
                purelog.write_log(f"Unable to demote file system: {fs['name']} - Setting to unwritable instead.", show_output=True)
            else:
                purelog.write_log(f"Other error occurred with code: {err.code}")

    watch.end_stopwatch()
