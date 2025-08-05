#!/usr/bin/env python3
import purefb_api as pfa
import json

# Initialize api sessions to each blade
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

def compare_nfs_rules():
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
    legacy_pols = legacy.get_snapshot_policies()
    s200_pols = s200.get_snapshot_policies()
    legacy_list = []
    s200_list = []
    for pol in legacy_pols:
        legacy_list.append(pol["name"])
    for pol in s200_pols:
        s200_list.append(pol["name"])
    for p in legacy_list:
        if p not in s200_list:
            print(f"Snapshot policy {p} not in s200 snapshot policies.")
            print()
        else:
            print(f"Snapshot policy {p} OK.")
            print()

def compare_filesystem_attached_snapshot_policies():
    legacy_policies = legacy.get_snapshot_policies()
    s200_policies = s200.get_snapshot_policies()

    legacy_policy_dict = {}
    for pol in legacy_policies:
        policy_name = pol["name"]
        legacy_policy_members = legacy.get_filesystems_attached_to_snapshot_policy(policy_name)
        members = []
        for member in legacy_policy_members:
            members.append(member["member"]["name"])

        legacy_policy_dict[policy_name] = members




if __name__ == "__main__":
    compare_filesystem_attached_snapshot_policies()
    

    
    