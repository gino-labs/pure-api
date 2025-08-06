#!/usr/bin/env python3
import pure_migration_v3 as pv3
import time

def Migrate_Subnets():
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

    s200_subs = pv3.Get_Subnets(auth_token_s200, pv3.PB2_MGT)

    s200_sub_names = []
    s200_sub_prefixes = []

    for s2sub in s200_subs:
        s200_sub_names.append(s2sub["name"])
        s200_sub_prefixes.append(s2sub["prefix"])

    subs = pv3.Get_Subnets(auth_token, pv3.PB1_MGT)

    sub_prefixes = []
    for sub in subs:
        sub_prefixes.append(sub["prefix"])

    for sub in subs:
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        if (sub["name"] in s200_sub_names) or (sub["prefix"] in s200_sub_prefixes):
            print(f"Subnet already exists: {sub['name']}, {sub['prefix']}")
            print()
            continue

        # Develop payload with sub
        payload = {
            "gateway": sub["gateway"],
            "link_aggregation_group": sub["link_aggregation_group"],
            "mtu": sub["mtu"],
            "prefix": sub["prefix"],
            "vlan": sub["vlan"],
        }

        post_check = pv3.Post_Subnet(sub["name"], auth_token_s200, pv3.PB2_MGT, payload)
    
    print("Subnets migrated.")
    print()

def Migrate_Interfaces():

    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    interfaces = pv3.Get_Interfaces(auth_token, pv3.PB1_MGT)

    ip_ints = []
    for iface in interfaces:
        ip_ints.append(iface["address"])

    for iface in interfaces:
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)
        
        iface_name = iface["name"]
        iface_check = pv3.Get_Single_Interface(iface_name, auth_token_s200, pv3.PB2_MGT)

        if iface_check["address"] in ip_ints:
            print(f"Interface with {iface_check['address']} already exists: {iface_name}")
            print()
            continue

        payload = {
            "address": iface["address"],
            "services": iface["services"],
        }

        post_check = pv3.Post_Interface(iface_name, auth_token_s200, pv3.PB2_MGT, payload)

        if post_check == 200:
            print(f"POST success for interface: {iface_name}.")
            print()
        else:
            print(f"Failed to POST: {iface_name}")
            print()
        time.sleep(3)

    print("Network Interfaces migrated.")
    print()

if __name__ == "__main__":
    Migrate_Subnets()
    # Don't migrate interfaces to avoid duplicate IPs!