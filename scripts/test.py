#!/usr/bin/env python3
import json
import time
from purefb_log import *
from purefb_api import *
from fbmigrate_configs import ConfigMigrator


if __name__ == "__main__":
    rrc_site = SiteVars()
    site_vars = rrc_site.get_site_vars() 
    legacy = FlashBladeAPI(site_vars["pb1"], site_vars["pb1_mgt"], site_vars["legacy_api_token"])
    s200 = FlashBladeAPI(site_vars["pb2"], site_vars["pb2_mgt"], site_vars["s200_api_token"])

    logger = PureLog()
    watch = Stopwatch()

    watch.start_stopwatch()

    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()

    # One off config migration + testing

    cfg_migrator = ConfigMigrator()

    cfg_migrator.migrate_config_subnets()

    watch.end_stopwatch()
