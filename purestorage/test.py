#!/usr/bin/env python3
import json
import time
import pure_migration_v3 as pv3


if __name__ == "__main__":
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT, message=False)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT, message=False)

    #pv3.Get_API_Versions(auth_token, pv3.PB1_MGT)
    #pv3.Get_API_Versions(auth_token_s200, pv3.PB2_MGT)

    result = pv3.Get_Single_Filesystem_Snapshot("pre-swap", auth_token, pv3.PB1_MGT)

    print(json.dumps(result, indent=4))