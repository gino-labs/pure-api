#!/usr/bin/env python3
import json
import pure_migration_v3 as pv3


if __name__ == "__main__":
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

    test = pv3.Get_Single_Filesystem("repos_linux_tucson", auth_token, pv3.PB1_MGT)

    print(json.dumps(test, indent=4))

    