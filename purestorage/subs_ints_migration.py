#!/usr/bin/env python3
import pure_migration_v3 as pv3

def Migrate_Subnets():
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    subs = pv3.Get_Subnets(auth_token, pv3.PB1_MGT)

    sub_names = []
    for sub in subs:
        sub_names.append(sub["name"])

    for sub in subs:
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        sub_check = pv3.Get_Single_Subnet(auth_token_s200, pv3.PB2_MGT)

        if sub_check["name"] in sub_names:
            print(f"Subnet already exists on destination: {sub_check["name"]}")
            print()
            continue

        # Develop payload with sub

if __name__ == "__main__":
    print("TODO")