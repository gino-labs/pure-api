#!/usr/bin/env python3
import pure_migration_v3 as pv3

# Script for migrating object storage related components #

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
            print(f"Object store account already exists. {acct_check}")
            print()
            continue

        # Develop post payload from existing object store account
        payload = {
            "bucket_defaults": acct["bucket_defaults"],
            "hard_limit_enabled": acct["hard_limit_enabled"],
            "quota_limit": acct["quota_limit"]
        }

        post_check = pv3.Post_Obj_Store_Account(auth_token_s200, pv3.PB2_MGT, acct_name, payload)

        if post_check is None:
            print(f"Post failed for {acct_name}")
            print()
    print("Done")



### main ###
if __name__ == "__main__":
    Obj_Account_Migration()



