#!/usr/bin/env python3
import pure_migration_v3 as pv3
import time
import json

# Get auth tokens
auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

# Get List of Filesystems to Demote on Legacy
filesystems = pv3.Get_Filesystems(auth_token, pv3.PB1_MGT)
filesystems = pv3.Get_Filesystems(auth_token_s200, pv3.PB2_MGT)

# For each filesystem disable / demote
payload = {
    "nfs": {
        "v3_enabled": False,
        "v4_1enabled": False
    },
    "writable": False
}
for fs in filesystems:
### pv3.Patch_Fs(fs["name"], auth_token, pv3.API_TOKEN, payload)
    print(f"Would patch {fs['name']} with the following json payload...\n")
    print(json.dumps(payload, indent=4))

# Get list of filesystems to Promote on S200

# For each filesystem enable / promote

# Get IPs from legacy

# Get IPs from s200

# Patch Legacy IPs to s200

# Patch s200 IPs to Legacy

# Disable replica links on Legacy
