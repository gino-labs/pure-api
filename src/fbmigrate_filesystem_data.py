#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *

'''
Example payload for legacy.post_filesystem_replica_link(filesystem, remote_array, payload)

payload = {
        "policies": [
            {
                "name": "5_mins",
                "location": {
                    "name": "bazpureblade1"
                }
            }
        ]
    }


Api Error info for handling error in this script
purefb_api.ApiError: [Code: 22] Replication is not supported for a file system that was created in a version prior to 3.0.0.
'''

'''
DONE / TEST

TODO / Optional
- Migrate file systems and their configurations
- Migrate file data with replication links
- Migrate file data with pcopy if replication not possible 
'''

# Logger object for logs
logger = PureLog()

# Stopwatch for script runtimes
watch = Stopwatch()

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# Create API object instances of each array
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

class FileSystemMigrator:
    def __init__(self):
        self.legacy = legacy
        self.s200 = s200
        self.logger = logger
        self.watch = watch