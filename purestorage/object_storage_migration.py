#!/usr/bin/env python3
import pure_migration_v3 as pv3
from jinja2 import Environment, FileSystemLoader
import subprocess
import time
import os

# Script for migrating object storage related components #

# Migrate object store accounts
def Obj_Account_Migration():
    # Get list of object accounts
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    acct_json_list = pv3.Get_Obj_Accounts(auth_token, pv3.PB1_MGT)

    for acct in acct_json_list:
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        acct_name = acct["name"]
        # Check if account name already exists on s200
        acct_check = pv3.Get_Single_Obj_Account(acct_name, auth_token_s200, pv3.PB2_MGT)

        if acct_check is not None:
            print(f"Object store account already exists: {acct_check['name']}")
            print()
            continue

        # Develop post payload from existing object store account
        if acct["bucket_defaults"]["quota_limit"] is not None:
            acct["bucket_defaults"]["quota_limit"] = str(acct["bucket_defaults"]["quota_limit"])
        if acct["quota_limit"] is not None:
            acct["quota_limit"] = str(acct["quota_limit"])

        payload = {
            "bucket_defaults": {
                "hard_limit_enabled": acct["bucket_defaults"]["hard_limit_enabled"],
                "quota_limit": acct["bucket_defaults"]["quota_limit"]
            },
            "hard_limit_enabled": acct["hard_limit_enabled"],
            "quota_limit": acct["quota_limit"]
        }

        post_check = pv3.Post_Obj_Account(auth_token_s200, pv3.PB2_MGT, acct_name, payload)

    print("Object store accounts done.")
    print()

# Migrate buckets
def Bucket_Migration():
    # Get list of object accounts
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    bucket_list = pv3.Get_Buckets(auth_token, pv3.PB1_MGT)

    for bucket in bucket_list:
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        bucket_name = bucket["name"]

        bucket_check = pv3.Get_Single_Bucket(bucket_name, auth_token_s200, pv3.PB2_MGT)

        if bucket_check is not None:
            print(f"Bucket already exists: {bucket_check['name']}")
            print()
            continue

        # Develop post payload from existing bucket
        if bucket["quota_limit"] is not None:
            bucket["quota_limit"] = str(bucket["quota_limit"])
        if bucket["object_lock_config"]["default_retention"] is not None:
            bucket["object_lock_config"]["default_retention"] = str(bucket["object_lock_config"]["default_retention"])

        payload = {
            "account": {
                "name": bucket["account"]["name"]
            },
            "bucket_type": bucket["bucket_type"],
            "hard_limit_enabled": bucket["hard_limit_enabled"],
            "object_lock_config": bucket["object_lock_config"],
            "quota_limit": bucket["quota_limit"],
            "retention_lock": bucket["retention_lock"]
        }

        post_check = pv3.Post_Bucket(auth_token_s200, pv3.PB2_MGT, bucket_name, payload)

    print("Buckets done.")
    print()

# Migrate object store account users
def Obj_Users_Migration():
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    users = pv3.Get_Obj_Users(auth_token, pv3.PB1_MGT)

    for user in users:
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        name = user["name"]

        user_check = pv3.Get_Single_Obj_User(name, auth_token_s200, pv3.PB2_MGT)

        if user_check is not None:
            print(f"User already exists: {user_check['name']}")
            print()
            continue
        # Develop Post payload

        # payload = {
        #     "name": name,
        #     "account": {
        #         "name": user["account"]["name"]
        #     }
        # }

        post_check = pv3.Post_Obj_User(auth_token_s200, pv3.PB2_MGT, name) #Removed payload
    
    print("Done.")
    print()


# Migrate Objects with temp users and temp keys
def Migrate_Objects():
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    accounts = pv3.Get_Obj_Accounts(auth_token, pv3.PB1_MGT)

    for acct in accounts:
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        user = f"{acct['name']}/migration"
        pv3.Post_Obj_User(auth_token, pv3.PB1_MGT, user)
        pv3.Post_Obj_User(auth_token_s200, pv3.PB2_MGT, user)

        existing_keys = pv3.Get_Obj_Access_Keys(auth_token, pv3.PB1_MGT)
        existing_keys_s200 = pv3.Get_Obj_Access_Keys(auth_token_s200, pv3.PB2_MGT)

        # Delete old migration keys if they exist
        for key in existing_keys:
            if "migration" in key["user"]["name"]:
                pv3.Delete_Access_Key(key["name"], auth_token, pv3.PB1_MGT)

        for key in existing_keys_s200:
            if "migration" in key["user"]["name"]:
                pv3.Delete_Access_Key(key["name"], auth_token_s200, pv3.PB2_MGT)

        payload = {
            "user": {
                "name": user
            }
        }

        # Returns a json body containing access key and secret key
        src_data = pv3.Post_Access_Key(auth_token, pv3.PB1_MGT, payload)
        dest_data = pv3.Post_Access_Key(auth_token_s200, pv3.PB2_MGT, payload)

        src_access = src_data["name"]
        src_secret = src_data["secret_access_key"]
        src_user = src_data["user"]["name"]

        dest_access = dest_data["name"]
        dest_secret = dest_data["secret_access_key"]
        dest_user = dest_data["user"]["name"]

        pv3.Save_Key_Info(src_user, src_access, src_secret, pv3.PB1_MGT)
        pv3.Save_Key_Info(dest_user, dest_access, dest_secret, pv3.PB2_MGT)

        # Start rclone process
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('rclone.conf.j2')

        config_data = {
            "access_key": src_access,
            "secret_key": src_secret,
            "data_ip": pv3.PB1,
            "access_key2": dest_access,
            "secret_key2": dest_secret,
            "data_ip2": pv3.PB2
        }

        rendered_output = template.render(config_data)

        with open("rclone.conf", "w") as config:
            config.write(rendered_output)

        buckets = pv3.Get_Buckets(auth_token_s200, pv3.PB2_MGT)
        
        acct_name = acct["name"]

        for bucket in buckets:
            if bucket["account"]["name"] == acct_name:
                buck = bucket["name"]
                break
            
        # Rclone subprocess
        try:
            subprocess.run(["rclone", "copy", f"srcfb:{buck}", f"destfb:{buck}", "--config", "rclone.conf", "--progress", "-vv", "--no-check-certificate"])
            print(f"Successful rclone of {acct_name} and {buck}")
            print()
            time.sleep(3)
        except Exception as e:
            print(f"Exception occured: {e}")

    os.remove("rclone.conf")
    print("Object migration finished.")
    print()
    time.sleep(3)
        

# account / user
def Test():
    print("Test Keys")


### main ###
if __name__ == "__main__":
    #Obj_Account_Migration()
    #Bucket_Migration()
    #Obj_Users_Migration()
    Migrate_Objects()





