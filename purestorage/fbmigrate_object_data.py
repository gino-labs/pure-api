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

    s200_acct_names = [acct["name"] for acct in s200_accts]

    for acct in accts:
        payload = {
            "bucket_defaults": acct["bucket_defaults"],
            "hard_limit_enabled": acct["hard_limit_enabled"],
            "quota_limit": acct["quota_limit"]
        }
        if acct["name"] not in s200_acct_names:
            s200.post_object_store_account(acct["name"], payload)

# Migrate buckets

# Migrate object store users

# Create new object store access/secret keys for users on both FBs (Save secrets for s200)

# Migrate object storage using rclone

# Establish object replication link after using s200 created keys

# Remove temporary object store users on legacy used for rclone