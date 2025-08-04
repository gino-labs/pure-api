#!/usr/bin/env python3
import purefb_api as pfa
import json

# Initialize api sessions to each blade
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

legacy_filesystems = legacy.get_filesystems()
s200_filesystems = s200.get_filesystems()

if len(legacy_filesystems) != len(s200_filesystems):
    print(f"Mismatch filesystems count. s200:{len(s200_filesystems)}, legacy:{len(legacy_filesystems)}")
    print()
    exit()

for fs in s200_filesystems:
    fs_name = fs["name"]
    nfs_rules = fs["nfs"]["rules"]
    legacy_nfs_rules = None
    for fs_legacy in legacy_filesystems:
        if fs_name == fs_legacy["name"]:
            legacy_nfs_rules = fs_legacy["nfs"]["rules"]
    if legacy_nfs_rules == None:
        print(f"Could not find matching filesystem named {fs_name}")
        print()
    elif legacy_nfs_rules not in nfs_rules:
        print(f"Legacy NFS rules not found in s200 filesystem: {fs_name}")
        print(f"s200: {json.dumps(nfs_rules)}")
        print(f"Legacy: {json.dumps(legacy_nfs_rules)}")
        print()
    else:
        print(f"NFS rules okay: {fs_name}")
        print()