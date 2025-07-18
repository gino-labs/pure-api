#!/usr/bin/env python3
import os
import json
import time
import tempfile
import subprocess
import pure_migration_v3 as pv3

if __name__ == "__main__":
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

    # Get List of Filesystems on Legacy #
    filesystems = []
    gxc = pv3.Get_Single_Filesystem("gxc_test", auth_token, pv3.PB1_MGT)
    filesystems.append(gxc)

    # Get list of filesystems to Promote on S200
    filesystems200 = []
    gxc2 = pv3.Get_Single_Filesystem("gxc_test", auth_token_s200, pv3.PB2_MGT)
    filesystems200.append(gxc2)

    fs_names = []
    for fs in filesystems:
        fs_names.append(fs["name"])

    fs200_names = []
    for fs in filesystems200:
        fs200_names.append(fs["name"])

    # Get Interface info from legacy #
    ifaces = []
    test1 = pv3.Get_Single_Interface("testing-link", auth_token, pv3.PB1_MGT)
    ifaces.append(test1)
    data_iface_names = []
    original_ips = [] # Orignal IPs to check on NFS clients

    for iface in ifaces:
        if "data" in iface["services"]:
            data_iface_names.append(iface["name"])
            original_ips.append(iface["address"])
        
    if len(original_ips) > 1:
        pure_ips = "|".join(original_ips)
    else:
        pure_ips = original_ips[0]
    
    # Get Interface info from s200 #
    ifaces_s200 = []
    test2 = pv3.Get_Single_Interface("testing-link", auth_token_s200, pv3.PB2_MGT)
    ifaces_s200.append(test2)
    data_iface_names_s200 = []

    for iface in ifaces_s200:
        if "data" in iface["services"]:
            data_iface_names_s200.append(iface["name"])

    # Patch Legacy IPs to s200
    for iface in ifaces:
        if iface["name"] in data_iface_names_s200:
            payload = { "address": iface["address"] }
            pv3.Patch_Interface(iface["name"], auth_token_s200, pv3.PB2_MGT, payload)

    # Patch s200 IPs to Legacy
    for iface in ifaces_s200:
        if iface["name"] in data_iface_names:
            payload = { "address": iface["address"] }
            pv3.Patch_Interface(iface["name"], auth_token, pv3.PB1_MGT, payload)

    # For each filesystem enable / promote
    for fs in filesystems200:
        if fs["name"] in fs_names:
            promote_payload = {
                "nfs": {
                    "v3_enabled": fs["nfs"]["v3_enabled"],
                    "v4_1_enabled": fs["nfs"]["v4_1_enabled"]
                },
                "http": {
                    "enabled": fs["http"]["enabled"]
                },
                "writable": True,
                "requested_promotion_state": "promoted"
            }

            pv3.Patch_Fs(fs["name"], auth_token, pv3.PB1_MGT, promote_payload)

    # Delete pre swap snapshots

    # Promote Legacy again

    # Set up Replica link again