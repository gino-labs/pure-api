#!/usr/bin/env python3
import pure_migration_v3 as pv3

# Script for migrating object storage related components #

# Migrate object store accounts
def Obj_Account_Migration():
    # Get list of object accounts
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    acct_json_list = pv3.Get_Obj_Store_Accounts(auth_token, pv3.PB1_MGT)

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

        post_check = pv3.Post_Obj_Store_Account(auth_token_s200, pv3.PB2_MGT, acct_name, payload)

    print("Object store accounts done.")
    print()

# Migrate buckets
def Bucket_Migration():
    # Get list of object accounts
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    bucket_list = pv3.Get_Buckets_Json(auth_token, pv3.PB1_MGT)

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

### main ###
if __name__ == "__main__":
    Obj_Account_Migration()
    Bucket_Migration()



