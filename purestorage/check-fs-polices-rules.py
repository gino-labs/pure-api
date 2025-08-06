#!/usr/bin/env python3
import purefb_api as pfa
import json
import time

# Initialize api sessions to each blade
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

def compare_nfs_rules():
    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()

    if len(legacy_filesystems) != len(s200_filesystems):
        print(f"Mismatch filesystems count. s200:{len(s200_filesystems)}, legacy:{len(legacy_filesystems)}")
        print()
        s200_list = []
        for fs in s200_filesystems:
            s200_list.append(fs["name"])
        for fs in legacy_filesystems:
            if fs["name"] not in s200_list:
                print(f"{fs['name']} not in s200 filesystems")
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
    # Get snapshot polices and filesystems
    legacy_policies = legacy.get_snapshot_policies()
    s200_policies = s200.get_snapshot_policies()
    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()

    # Initialize policy dictionary with policy key, and filsystems list value
    legacy_policy_dict = {}
    for fs in legacy_filesystems:
        fs_name = fs["name"]
        legacy_policy_dict[fs_name] = []

    # Add members associated with policy to their respective list
    for pol in legacy_policies:
        policy_name = pol["name"]
        legacy_policy_members = legacy.get_filesystems_attached_to_snapshot_policy(policy_name)
        for member in legacy_policy_members:
            member_name = member["member"]["name"]
            legacy_policy_dict[member_name].append(policy_name)

    # Initialize policy dictionary with policy key, and filsystems list value
    s200_policy_dict = {}
    for fs in s200_filesystems:
        fs_name = fs["name"]
        s200_policy_dict[fs_name] = []

    # Add members associated with policy to their respective list
    for pol in s200_policies:
        policy_name = pol["name"]
        s200_policy_members = s200.get_filesystems_attached_to_snapshot_policy(policy_name)
        for member in s200_policy_members:
            member_name = member["member"]["name"]
            s200_policy_dict[member_name].append(policy_name)

    # Print filesystems along with missing snapshot polices
    for filesystem, policies in legacy_policy_dict.items():
        fs_missing_policies = []
        for policy in policies:
            if policy not in s200_policy_dict[filesystem]:
                fs_missing_policies.append(policy)
        if fs_missing_policies:
            print(f"{filesystem} MISSING policies: {fs_missing_policies}")
            print()
        else:
            print(f"{filesystem} policies OK")       

if __name__ == "__main__":
    compare_nfs_rules()
    compare_snapshot_policies()
    compare_filesystem_attached_snapshot_policies()
    

    
    