#!/usr/bin/env python3
import json
import time
import pure_migration_v3 as pv3


if __name__ == "__main__":
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

    pv3.Get_API_Versions(auth_token, pv3.PB1_MGT)
    pv3.Get_API_Versions(auth_token_s200, pv3.PB2_MGT)

    clients = pv3.Get_NFS_Clients(auth_token, pv3.PB1_MGT)

    print(json.dumps(clients, indent=4))
    print(len(clients))
