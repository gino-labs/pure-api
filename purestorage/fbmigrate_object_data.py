#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader
import purefb_api as pfa
import purefb_log as pfl
import subprocess
import os

# Migrate object store accounts
def migrate_object_store_accounts():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    accts = legacy.get_object_store_accounts()
    s200_accts = s200.get_object_store_accounts()

    # List of s200 object store account names
    s200_acct_names = [acct["name"] for acct in s200_accts]

    # Post each account not in s200 account names
    for acct in accts:
        if acct["name"] not in s200_acct_names:
            payload = {
                "bucket_defaults": acct["bucket_defaults"],
                "hard_limit_enabled": acct["hard_limit_enabled"],
                "quota_limit": acct["quota_limit"]
            }
            s200.post_object_store_account(acct["name"], payload)

# Migrate buckets
def migrate_buckets():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    buckets = legacy.get_buckets()
    s200_buckets = s200.get_buckets()

    # List of s200 bucket names
    s200_buckets_names = [bucket["name"] for bucket in s200_buckets]

    # Post each bucket not in s200 bucket names
    for bucket in buckets:
        if bucket["name"] not in s200_buckets_names:
            payload = {
                "account": bucket["account"],
                "bucket_type": bucket["bucket_type"],
                "hard_limit_enabled": bucket["hard_limit_enabled"],
                "object_lock_config": bucket["object_lock_config"],
                "quota_limit": bucket["quota_limit"],
                "retention_lock": bucket["unlocked"]
            }
            s200.post_bucket(bucket["name"], payload)
        


# Migrate object store users

# Create new object store access/secret keys for users on both FBs (Save secrets for s200)

# Migrate object storage using rclone

# Establish object replication link after using s200 created keys

# Remove temporary object store users on legacy used for rclone