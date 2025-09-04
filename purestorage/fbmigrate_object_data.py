#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import purefb_api as pfa
import purefb_log as pfl
import subprocess
import json
import os

script_logger = pfl.PureLog()

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
    s200_bucket_names = [bucket["name"] for bucket in s200_buckets]

    # Post each bucket not in s200 bucket names
    for bucket in buckets:
        if bucket["name"] not in s200_bucket_names:
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
def migrate_object_store_users():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    users = legacy.get_object_store_users()
    s200_users = s200.get_object_store_users()

    # List of s200 object store user names
    # FIXME empty list can't access
    s200_user_names = [user["name"] for user in s200_users]

    # Post each user not in s200 user names
    for user in users:
        if user["name"] not in s200_user_names and "migration" not in user["name"]:
            s200.post_object_store_user(user["name"])

# Create new object store access/secret keys for users on both FBs (Save secrets for s200)
def create_new_s200_access_keys():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    users = legacy.get_object_store_users()
    s200_users = s200.get_object_store_users()

    # List of object store user names
    legacy_user_names = [user["name"] for user in users]

    key_data= []
    # Post new access keys from migrated users
    for user in s200_users:
        if user["name"] in legacy_user_names and not user["access_keys"]:
            payload = {
                "user": {
                    "name": user
                }
            }
            # Post new access key and append to list
            new_key_entry = s200.post_object_store_access_key(user["name"], payload)
            key_data.append(new_key_entry)

    # Save key data to file in .secrets directory
    os.makedirs(".secrets", exist_ok=True)
    today = f"{datetime.now().strftime('%d%b%Y')}"
    with open(".secrets/s200_access_keys.json", "w") as file:
        json.dump(key_data, file, indent=4)

# Create temporary users on legacy for migrating objects
def create_migration_legacy_users_and_keys():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    accts = legacy.get_object_store_accounts()

    acct_names = [accts["name"] for acct in accts]

    # For each account create a temporaray migration user
    migration_users = []
    for acct in acct_names:
        migration_user = f"{acct}/migration" 
        legacy.post_object_store_user(migration_user)
        migration_users.append(migration_user)

    # For each migration user create a temporary access key
    migration_keys = []
    for user in migration_users:
        payload = {
                "user": {
                    "name": user
                }
            }
        migration_key = legacy.post_object_store_access_key(user, payload)
        migration_keys.append(migration_key)
    
    # Write to temporary file
    with open(".secrets/migration_keys.json", "w") as file:
        json.dump(migration_keys, file, indent=4)

# Migrate object storage using rclone
def rclone_object_storage_buckets():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    buckets = legacy.get_buckets()
    users = legacy.get_object_store_users()

    s200_users = s200.get_object_store_users()

    # Load saved json keys created by earlier functions
    with open(".secrets/migration_keys.json", "r") as file:
        legacy_migration_keys = json.load(file)

    with open(".secrets/s200_access_keys.json", "r") as file:
        s200_migration_keys = json.load(file)
    
    # For each bucket, determine the associated account, then the associated user to use with the proper credentials
    for bucket in buckets:
        bucket_account = bucket["account"]["name"]

        for user in users:
            if user["account"]["name"] == bucket_account and "migration" in user["account"]["name"]:
                matching_legacy_user = user
                break
                
        for key in legacy_migration_keys:
            if key["user"]["name"] == matching_legacy_user["name"]:
                legacy_key = key
                break

        for user in s200_users:
            if user["account"]["name"] == bucket_account:
                matching_s200_user = user
                break

        for key in s200_migration_keys:
            if key["user"]["name"] == matching_s200_user["name"]:
                s200_key = key
                break
        
        # Using rclone.conf.j2 jinja template to render with config data
        config_data = {
            "access_key_src": legacy_key["name"],
            "secret_key_src": legacy_key["secret_access_key"],
            "data_ip_src": legacy.data_ip,
            "access_key_dest": s200_key["name"],
            "secret_key_dest": s200_key["secreat_access_key"],
            "data_ip_dest": s200.data_ip
        }

        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('rclone.conf.j2')
        rendered_output = template.render(config_data)

        with open("rclone.conf", "w") as file:
            file.write(rendered_output)

        # Use subprocess module to run rclone process
        rclone_cmd = ["rclone", "copy", f"srcfb:{bucket['name']}", f"destfb:{bucket['name']}", "--config", "rclone.conf", "--progress", "-vv", "--no-check-certificate"]
        try:
            subprocess.run(rclone_cmd)
            msg = f"Rclone success for {bucket['name']}"
            script_logger.write_log(msg)
            print(msg)
            print()
        except Exception as e:
            print(f"Excpetion has occured trying to rclone {bucket['name']}: {e}")
            print()

    # After each bucket has been rcloned remove the last rclone.conf
    os.remove("rclone.conf")

# Remove temporary object store users on legacy used for rclone
def remove_temporary_migration_users():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)

    users = legacy.get_object_store_users()

    for user in users:
        if "migration" in user["name"]:
            legacy.delete_object_store_user(user["name"])
    os.remove(".secrets/migration_keys.json")

# Add remote credentials from s200 to source
def add_remote_credentials():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)

    # Add remote credentials to legacy from s200 using json file in .secrets
    with open(".secrets/s200_access_keys.json", "r") as file:
        s200_credentials = json.load(file)

    for cred in s200_credentials:
        access_key = cred["name"]
        secret_key = cred["secret_access_key"]
        account_user = cred["user"]["name"].replace("/", "-")

        payload = {
            "access_key_id": access_key,
            "secret_access_key": secret_key
        }
        legacy.post_object_store_remote_credential(account_user, payload)

# Establish bucket replica links, enable object versioning on buckets
def create_bucket_replica_links():
    legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    buckets = legacy.get_buckets()
    s200_buckets = s200.get_buckets()
    credentials = legacy.get_object_store_remote_credentials()

    with open(".secrets/s200_access_keys.json") as f:
        s200_credentials = json.load(f)

    # Enabled versioning on each s200 bucket
    for bucket in s200_buckets:
        payload = {
            "versioning": "enabled"
        }
        s200.patch_bucket(bucket["name"], payload)

    # For each bucket on legacy establish replica link to remote s200
    for bucket in buckets:
        account = bucket["account"]["name"]

        for cred in credentials:
            if account in cred["name"]:
                replication_credential = cred
                break
    
        # Enable versioning on the bucket (Required for object replication)
        payload = {
            "versioning": "enabled"
        }
        legacy.patch_bucket(bucket["name"], payload)

        # Post new bucket replica link with a valid credential
        payload = {
            "paused": False,
            "cascading_enabled": False
        }
        
        legacy.post_bucket_replica_link(bucket["name"], replication_credential["name"], payload)
                
        
# Main Script
if __name__ == "__main__":
    # Fucntion call to migrate object store accounts
    migrate_object_store_accounts()

    # Function call to migrate object store buckets
    migrate_buckets()

    # Fucntion call to migrate object store users
    migrate_object_store_users()

    # Function call to create new access keys on migrated s200 users
    create_new_s200_access_keys()
        
    # Fucntion call to create tempoary migration users and keys on legacy
    create_migration_legacy_users_and_keys()

    # Fucntion call to move object storage with rclone
    rclone_object_storage_buckets()

    # Function call to remove temporary created users/files
    remove_temporary_migration_users()

    # Function call to add remote credentials on legacy for object replication
    add_remote_credentials()

    # Function call to create the bucket replica links
    create_bucket_replica_links()
