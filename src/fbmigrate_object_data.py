#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader
from purefb_api import *
from purefb_log import *
import subprocess
import json
import os

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

class ObjectMigrator:
    def __init__(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)
        self.logger = PureLog()
        self.watch = Stopwatch()

    def refresh_api_session(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)

    # Migrate object store accounts #
    def migrate_object_store_accounts(self):
        self.logger.write_log("Migrating Object store accounts", show_output=True)

        accts = self.legacy.get_object_store_accounts()
        s200_accts = self.s200.get_object_store_accounts()

        # List of s200 object store account names
        if not s200_accts:
            s200_acct_names = []
        elif isinstance(s200_accts, dict):
            s200_acct_names = [s200_accts["name"]]
        else:
            s200_acct_names = [acct["name"] for acct in s200_accts]

        # Post each account not in s200 account names
        accts_migrated = []
        for acct in accts:
            # Idempotent check
            if acct["name"] not in s200_acct_names:
                if acct["bucket_defaults"]["quota_limit"]:
                    bd_quota_limit = str(acct["bucket_defaults"]["quota_limit"])
                else:
                    bd_quota_limit = ""

                if acct["quota_limit"]:
                    quota_limit = str(acct["quota_limit"])
                else:
                    quota_limit = ""

                payload = {
                    "bucket_defaults": { 
                        "hard_limit_enabled": acct["bucket_defaults"]["hard_limit_enabled"],
                        "quota_limit": bd_quota_limit
                    },
                    "hard_limit_enabled": acct["hard_limit_enabled"],
                    "quota_limit": quota_limit
                }
                self.s200.post_object_store_account(acct["name"], payload)
                accts_migrated.append(acct["name"])
        return accts_migrated

    # Migrate buckets #
    def migrate_buckets(self):
        self.logger.write_log("Migrating buckets", show_output=True)

        buckets = self.legacy.get_buckets()
        s200_buckets = self.s200.get_buckets()

        # List of s200 bucket names
        if not s200_buckets:
            s200_bucket_names = []
        elif isinstance(s200_buckets, dict):
            s200_bucket_names = [s200_buckets["name"]]
        else:
            s200_bucket_names = [bucket["name"] for bucket in s200_buckets]

        # Post each bucket not in s200 bucket names
        buckets_migrated = []
        for bucket in buckets:
            # Idempotent check
            if bucket["name"] not in s200_bucket_names:
                if bucket["object_lock_config"]["default_retention"]:
                    default_retention = str(bucket["object_lock_config"]["default_retention"])
                else:
                    default_retention = ""

                if bucket["quota_limit"]:
                    quota_limit = str(bucket["quota_limit"])
                else:
                    quota_limit = ""
                
                account = bucket["account"]["name"]
                payload = {
                    "account": {
                        "name": account
                    },
                    "bucket_type": bucket["bucket_type"],
                    "hard_limit_enabled": bucket["hard_limit_enabled"],
                    "object_lock_config": {
                        "default_retention_mode": bucket["object_lock_config"]["default_retention_mode"],
                        "enabled": bucket["object_lock_config"]["enabled"],
                        "freeze_locked_objects": bucket["object_lock_config"]["freeze_locked_objects"],
                        "default_retention": default_retention
                    },
                    "quota_limit": quota_limit,
                    "retention_lock": bucket["retention_lock"]
                }
                self.s200.post_bucket(bucket["name"], payload)
                buckets_migrated.append(bucket["name"])
        return buckets_migrated
        
    # Migrate object store users #
    def migrate_object_store_users(self):
        self.logger.write_log("Migrating objct store Users", show_output=True)

        users = self.legacy.get_object_store_users()
        s200_users = self.s200.get_object_store_users()

        # List of s200 object store user names if any
        if not s200_users:
            s200_user_names = []
        elif isinstance(s200_users, dict):
            s200_user_names = [s200_users["name"]]
        else:
            s200_user_names = [user["name"] for user in s200_users]

        # Post each user not in s200 user names
        users_migrated = []
        for user in users:
            # Idempotent check
            if user["name"] not in s200_user_names and "migration" not in user["name"]:
                self.s200.post_object_store_user(user["name"])
                users_migrated.append(user["name"])
        return users_migrated

    # Create new object store access/secret keys for users on both FBs (Save secrets for s200)
    def create_new_s200_access_keys(self):
        self.logger.write_log("Creating new s200 access keys", show_output=True)

        users = self.legacy.get_object_store_users()
        s200_users = self.s200.get_object_store_users()

        # List of object store user names
        if isinstance(users, dict):
            legacy_user_names = [users["name"]]
        else:
            legacy_user_names = [user["name"] for user in users]

        double_access_key_list = []
        s200_keys = self.s200.get_object_store_access_keys()

        if s200_keys and not isinstance(s200_keys, dict):
            single_access_key_list = []
            for key in s200_keys:
                if key["user"]["name"] in single_access_key_list:
                    double_access_key_list.append(key["user"]["name"])
                else:
                    single_access_key_list.append(key["user"]["name"])

        # Check if keys already exist for user
        if s200_keys:
            s200_key_user_list = [key["user"]["name"] for key in s200_keys]
        else:
            s200_key_user_list = []
            
        new_key_data= []
        # Post new access keys from migrated users
        for user in s200_users:
            # Idempotent check
            if user["name"] in s200_key_user_list:
                print(f"User {user['name']} already has an access key.")
                print()
                continue
            if user["name"] in legacy_user_names:
                payload = {
                    "user": {
                        "name": user["name"]
                    }
                }
                # Post new access key and append to list
                new_key_entry = self.s200.post_object_store_access_key(user["name"], payload)
                new_key_data.append(new_key_entry)    

        os.makedirs(".secrets", exist_ok=True)

        if new_key_data:
            if os.path.exists(f".secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json"):
                with open(f".secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json", "r") as f:
                    existing_keys = json.load(f)    
                key_data = [key for key in existing_keys]
                for key in new_key_data:
                    key_data.append(key)
            else:
                key_data = new_key_data
            with open(f".secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json", "w") as file:
                json.dump(key_data, file, indent=4)
            print(f"S200 keys have been saved to .secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json.")
            print()
        else:
            print(f"s200 keys already exist, check .secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json")
            print()

    # Create temporary users on legacy for migrating objects
    def create_migration_legacy_users_and_keys(self):
        self.logger.write_log("Creating legacy migration users and keys", show_output=True)

        accts = self.legacy.get_object_store_accounts()
        users = self.legacy.get_object_store_users()

        for user in users:
            if "migration" in user["name"]:
                self.legacy.delete_object_store_user(user["name"])

        if isinstance(accts, dict):
            acct_names = [accts["name"]]
        else:
            acct_names = [acct["name"] for acct in accts]

        # For each account create a temporaray migration user
        migration_users = []
        for acct in acct_names:
            migration_user = f"{acct}/migration" 
            self.legacy.post_object_store_user(migration_user)
            migration_users.append(migration_user)

        # For each migration user create a temporary access key
        migration_keys = []
        for user in migration_users:
            payload = {
                    "user": {
                        "name": user
                    }
                }
            migration_key = self.legacy.post_object_store_access_key(user, payload)
            migration_keys.append(migration_key)

        # Write to temporary file
        with open(".secrets/migration_keys.json", "w") as file:
            json.dump(migration_keys, file, indent=4)

    # Migrate object storage using rclone
    def rclone_object_storage_buckets(self):
        self.logger.write_log("Rclone object storage", show_output=True)

        buckets = self.legacy.get_buckets()
        users = self.legacy.get_object_store_users()

        s200_users = self.s200.get_object_store_users()

        # Load saved json keys created by earlier functions
        with open(".secrets/migration_keys.json", "r") as file:
            legacy_migration_keys = json.load(file)

        with open(f".secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json", "r") as file:
            s200_migration_keys = json.load(file)

        # For each bucket, determine the associated account, then the associated user to use with the proper credentials
        for bucket in buckets:
            self.refresh_api_session()
            bucket_account = bucket["account"]["name"]
            
            matching_legacy_user = None
            for user in users:
                # Same account for user and bucket, and migration in user name
                if user["account"]["name"] == bucket_account and "migration" in user["name"]:
                    matching_legacy_user = user
                    self.logger.write_log(f"Using legacy user: {matching_legacy_user['name']}", show_output=True)
                    break

            legacy_key = None      
            for key in legacy_migration_keys:
                if matching_legacy_user and key["user"]["name"] == matching_legacy_user["name"]:
                    legacy_key = key
                    self.logger.write_log(f"Using legacy key: {key['user']['name']} - {legacy_key['name']}", show_output=True)
                    break
            
            matching_s200_user = None
            for user in s200_users:
                if user["account"]["name"] == bucket_account:
                    matching_s200_user = user
                    self.logger.write_log(f"Using s200 user: {matching_s200_user['name']}", show_output=True)
                    break
            
            s200_key = None
            for key in s200_migration_keys:
                if matching_s200_user and key["user"]["name"] == matching_s200_user["name"]:
                    s200_key = key
                    self.logger.write_log(f"Using s200 key: {s200_key['user']['name']} - {s200_key['name']}", show_output=True)
                    break

            # Using rclone.conf.j2 jinja template to render with config data
            if s200_key and legacy_key:
                config_data = {
                    "access_key_src": legacy_key["name"],
                    "secret_key_src": legacy_key["secret_access_key"],
                    "data_ip_src": rrc_site.get_pb1_data_host(),
                    "access_key_dest": s200_key["name"],
                    "secret_key_dest": s200_key["secret_access_key"],
                    "data_ip_dest": rrc_site.get_pb2_data_host()
                }
            else:
                sys.exit("No migration keys found for either s200 or legacy.")

            env = Environment(loader=FileSystemLoader('ansible/templates'))
            template = env.get_template('rclone.conf.j2')
            rendered_output = template.render(config_data)

            with open("rclone.conf", "w") as file:
                file.write(rendered_output)

            # Use subprocess module to run rclone process
            rclone_cmd = ["rclone", "copy", f"srcfb:{bucket['name']}", f"destfb:{bucket['name']}", "--config", "rclone.conf", "--checkers=32","--progress", "-vv", "--no-check-certificate"]
            try:
                subprocess.run(rclone_cmd)
                print()
                msg = f"Rclone success for {bucket['name']}"
                self.logger.write_log(msg, show_output=True)
            except Exception as e:
                self.logger.write_log(f"Exception has occured trying to rclone {bucket['name']}: {e}", show_output=True)

        # After each bucket has been rcloned remove the last rclone.conf
        os.remove("rclone.conf")

    # Remove temporary object store users on legacy used for rclone
    def remove_temporary_migration_users(self):
        self.refresh_api_session()
        self.logger.write_log("Remove temporary migration users on legacy", show_output=True)

        users = self.legacy.get_object_store_users()

        for user in users:
            if "migration" in user["name"]:
                self.legacy.delete_object_store_user(user["name"])
        os.remove(".secrets/migration_keys.json")

        # Add remote credentials from s200 to source
    def add_remote_credentials(self):
        self.logger.write_log("Add remote credentials from s200 to legacy", show_output=True)

        remote_creds = self.legacy.get_object_store_remote_credentials()

        if remote_creds:
            if isinstance(remote_creds, dict):
                cred_remote_names = [remote_creds["name"]]
            else:
                cred_remote_names = [cred["name"] for cred in remote_creds]
        else:
            cred_remote_names = []

        # Add remote credentials to legacy from s200 using json file in .secrets
        with open(f".secrets/{rrc_site.get_pb2_name()}_s200_access_keys.json", "r") as file:
            s200_credentials = json.load(file)

        for cred in s200_credentials:
            access_key = cred["name"]
            secret_key = cred["secret_access_key"]
            account_user = cred["user"]["name"].replace("/", "-")

            self.logger.write_log(f"Posting remote credential from s200 to legacy: {account_user}", show_output=True)

            payload = {
                "access_key_id": access_key,
                "secret_access_key": secret_key
            }

            legacy_array_connections = self.legacy.get_array_connections()
            remote_name = legacy_array_connections["remote"]["name"]
            cred_name = f"{remote_name}/{account_user}"

            # Idempotent check
            if cred_name in cred_remote_names:
                continue


            self.legacy.post_object_store_remote_credential(cred_name, payload)

    # Establish bucket replica links, enable object versioning on buckets
    def create_bucket_replica_links(self):
        self.logger.write_log("Creating bucket replica links", show_output=True)

        buckets = self.legacy.get_buckets()
        s200_buckets = self.s200.get_buckets()
        credentials = self.legacy.get_object_store_remote_credentials()
        replica_links = self.legacy.get_bucket_replia_links()

        if replica_links:
            if isinstance(replica_links, dict):
                buckets_with_links = [replica_links["local_bucket"]["name"]]
            else:
                buckets_with_links = [link["local_bucket"]["name"] for link in replica_links]
        else:
            buckets_with_links = []

        # Enabled versioning on each s200 bucket
        for bucket in s200_buckets:
            payload = {
                "versioning": "enabled"
            }
            self.s200.patch_bucket(bucket["name"], payload)

        # For each bucket on legacy establish replica link to remote s200
        buckets_linked = 0
        for bucket in buckets:
            # Idempotent check
            if bucket["name"] in buckets_with_links:
                continue
            account = bucket["account"]["name"]

            replication_credential = None
            for cred in credentials:
                if account in cred["name"]:
                    replication_credential = cred
                    break

            # Enable versioning on the bucket (Required for object replication)
            payload = {
                "versioning": "enabled"
            }
            self.legacy.patch_bucket(bucket["name"], payload)

            # Post new bucket replica link with a valid credential
            payload = {
                "paused": False,
                "cascading_enabled": False
            }
            
            if replication_credential:
                self.legacy.post_bucket_replica_link(bucket["name"], replication_credential['name'], payload)
                buckets_linked += 1
            else:
                self.logger.write_log(f"Replication credential not found for {bucket['name']}")

        if buckets_linked == 0:
            self.logger.write_log("Bucket Replica links already established.", show_output=True)
        else:
            self.logger.write_log(f"Bucket replica links update: {buckets_linked}", show_output=True)

    # Delete object replica links on LEGACY for fresh reset
    def delete_legacy_object_replica_links(self):
        self.logger.write_log("Deleting Legacy bucket replica links for fresh reset", show_output=True)

        legacy_array_connections = self.legacy.get_array_connections()
        remote_name = legacy_array_connections["remote"]["name"]
        bucket_links = self.legacy.get_bucket_replia_links()

        for link in bucket_links:
            self.legacy.delete_bucket_replica_link(link["local_bucket"]["name"], remote_name)

        # Delete legacy remote credentials
        for cred in self.legacy.get_object_store_remote_credentials():
            self.legacy.delete_object_store_remote_credential(cred["name"])

    # Delete S200 access keys for fresh reset 
    def delete_s200_access_keys(self):
        self.logger.write_log("Deleting S200 access keys for fresh reset", show_output=True)

        keys = self.s200.get_object_store_access_keys()

        for key in keys:
            self.s200.delete_object_store_access_key(key["name"])
                    
# Main
if __name__ == "__main__":
    # Object Migrator instance
    obj_migrator = ObjectMigrator()

    # Object migration operations
    obj_migrator.delete_legacy_object_replica_links()
    obj_migrator.delete_s200_access_keys()
    obj_migrator.migrate_object_store_accounts()
    obj_migrator.migrate_buckets()
    obj_migrator.migrate_object_store_users()
    obj_migrator.create_new_s200_access_keys()
    obj_migrator.create_migration_legacy_users_and_keys()
    obj_migrator.rclone_object_storage_buckets()
    obj_migrator.remove_temporary_migration_users()
    obj_migrator.add_remote_credentials()
    obj_migrator.create_bucket_replica_links()
