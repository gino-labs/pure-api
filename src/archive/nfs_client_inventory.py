#!/usr/bin/env python3
import sys
import json
import scripts.old.pure_migration_v3 as pv3


def get_inventory(s200=False):
    if s200:
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT, message=False)
        clients = pv3.Get_NFS_Clients(auth_token, pv3.PB2_MGT, message=False)
    else:
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT, message=False)
        clients = pv3.Get_NFS_Clients(auth_token, pv3.PB1_MGT, message=False)

    hosts = []
    for client in clients:
        host = client["name"]
        if "172.20.0." not in host:
            host = host.split(":")[0]
            hosts.append(host)

    inventory = {
        "all": {
            "hosts": hosts
        }
    }

    return inventory

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        inventory = get_inventory()
        print(json.dumps(inventory, indent=4))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        print(json.dumps({}))
    else:
        print(json.dumps({}))

