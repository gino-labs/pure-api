#!/usr/bin/env python3
import purefb_api as pfa
import purefb_log as pfl

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