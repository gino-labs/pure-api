#!/usr/bin/env python3
import purefb_api as pfa
import json

def compare_nfs_rules():
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
            print(f"Legacy filesystem {fs_name} NFS rules not found in s200 filesystem:")
            print()
            rules_list = nfs_rules.split(" ")
            legacy_rules_list = legacy_nfs_rules.split(" ")
            for rule in legacy_rules_list:
                if rule not in rules_list:
                    print(rule)
            print()
        else:
            print(f"NFS rules OK: {fs_name}")
            print()

def check_export_policies():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    legacy_filesystems = legacy.get_filesystems()
    for fs in legacy_filesystems:
        if fs["nfs"]["export_policy"]["name"] == None:
            print(f"{fs['name']} export policy is null.")
            print()
        else:
            print(f"{fs['name']} export policy is present.")
            print(json.dumps(fs["nfs"]["export_policy"], indent=4))
            print()

def compare_snapshot_policies():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    legacy.get_snapshot_policies(dumpjson=True)

if __name__ == "__main__":
    compare_snapshot_policies()
    

    
    