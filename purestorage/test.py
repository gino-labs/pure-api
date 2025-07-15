#!/usr/bin/env python3
import json
import pure_migration_v3 as pv3


if __name__ == "__main__":
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

    pv3.Get_API_Versions(auth_token, pv3.PB1_MGT)
    pv3.Get_API_Versions(auth_token_s200, pv3.PB2_MGT)
    '''
    fs = pv3.Get_Single_Filesystem("gxc-testing", auth_token, pv3.PB1_MGT)
    
    del fs["promotion_status"]
    del fs["created"]
    del fs["source"]
    del fs["id"]
    del fs["space"]
    del fs["time_remaining"]
    del fs["destroyed"]
    del fs["name"]
    del fs["requested_promotion_state"]
    del fs["smb"]
    '''
    
    # fs = pv3.Get_Single_Filesystem("gxc_test", auth_token, pv3.PB1_MGT)
    # print(json.dumps(fs, indent=4))
    # exit()

    payload = {
        "policies": [
            {
                "name": "5_min"
            }
        ]
    }

    pv3.Post_Filesystem_Replica_Link("gxc_test", "vapureblade", auth_token, pv3.PB1_MGT, payload)

    link = pv3.Get_Single_Filesystem_Replica_Link("gxc_test", auth_token, pv3.PB1_MGT)
    print(json.dumps(link, indent=4))

    pv3.Delete_Filesystem_Replica_Link("gxc_test", auth_token, pv3.PB1_MGT)

    link = pv3.Get_Single_Filesystem_Replica_Link("gxc_test", auth_token, pv3.PB1_MGT)
    if link is not None:
        print(json.dumps(link, indent=4))


    #pv3.Post_Filesystem(auth_token_s200, pv3.PB2_MGT, "gxc-testing", fs)
    
    
    