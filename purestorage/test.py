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

    purelog.write_log("TEST: See API versions for legacy as json.", jsondata=vers)
    purelog.write_log("Another test to see appended output.")
    purelog.write_log("Bye World!")
