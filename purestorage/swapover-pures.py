#!/usr/bin/env python3
import pure_migration_v3 as pv3
import time
import json

# Get auth tokens
auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)


# Get List of Filesystems to Demote on Legacy
filesystems = pv3.Get_Filesystems(auth_token, pv3.PB1_MGT)


# Create final snapshots prior to continuing swap
for fs in filesystems:
    pv3.Post_Filesystem_Snapshot(fs["name"], auth_token, pv3.PB1_MGT, "pre-swap")

print("\nAllowing 5 seconds for snapshots to settle...\n")
time.sleep(5)


# For each legacy filesystem disable / demote
demote_payload = {
    "writable": False,
    "requested_promotion_state": "demoted"
}
for fs in filesystems:
    pv3.Patch_Fs(fs["name"], auth_token, pv3.API_TOKEN, demote_payload)


# Get Interface info from legacy
ifaces = pv3.Get_Interfaces(auth_token, pv3.PB1_MGT)
data_iface_names = []

for iface in ifaces:
    if "data" in iface["services"]:
        data_iface_names.append(iface["name"])


# Get Interface info from s200
ifaces_s200 = pv3.Get_Interfaces(auth_token_s200, pv3.PB2_MGT)
data_iface_names_s200 = []

for iface in ifaces_s200:
    if "data" in iface["services"]:
        data_iface_names_s200.append(iface["name"])


# Patch Legacy IPs to s200
for iface in ifaces:
    if iface["name"] in data_iface_names_s200:
        payload = { "address": iface["address"]}
        pv3.Patch_Interface(iface["name"], auth_token_s200, pv3.PB2_MGT, payload)


# Patch s200 IPs to Legacy
for iface in ifaces_s200:
    if iface["name"] in data_iface_names:
        payload = { "address": iface["address"]}
        pv3.Patch_Interface(iface["name"], auth_token, pv3.PB1_MGT, payload)


# Disable replica links on Legacy
links = pv3.Get_Filesystem_Replica_Links(auth_token, pv3.PB1_MGT)

for link in links:
    pv3.Delete_Filesystem_Replica_Link(link["id"], auth_token, pv3.PB1_MGT)


# Get list of filesystems to Promote on S200
filesystems200 = pv3.Get_Filesystems(auth_token_s200, pv3.PB2_MGT)

fs200_names = []
for fs in filesystems200:
    fs200_names.append(fs["name"])


# For each filesystem enable / promote
for fs in filesystems:
    if fs["name"] in fs200_names:
        promote_payload = {
            "nfs": {
                "v3_enabled": fs["nfs"]["v3_enabled"],
                "v4_1_enabled": fs["nfs"]["v4_1_enabled"]
            },
            "http": {
                fs["enabled"]["http"]
            },
            "writable": True,
            "requested_promotion_state": "promoted"
        }

        pv3.Patch_Fs(fs["name"], auth_token_s200, pv3.PB2_MGT, promote_payload)