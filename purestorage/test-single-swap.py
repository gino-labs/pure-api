#!/usr/bin/env python3
import os
import json
import time
import tempfile
import subprocess
import pure_migration_v3 as pv3


if __name__ == "__main__":
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

    # Get List of Filesystems on Legacy #
    filesystems = []
    gxc = pv3.Get_Single_Filesystem("gxc_test", auth_token, pv3.PB1_MGT)
    filesystems.append(gxc)

    # Get list of filesystems to Promote on S200 #
    filesystems200 = []
    gxc2 = pv3.Get_Single_Filesystem("gxc_test", auth_token_s200, pv3.PB2_MGT)
    filesystems200.append(gxc2)

    fs200_names = []
    for fs in filesystems200:
        fs200_names.append(fs["name"])

    # Get Interface info from legacy #
    ifaces = []
    test1 = pv3.Get_Single_Interface("testing-link", auth_token, pv3.PB1_MGT)
    ifaces.append(test1)
    data_iface_names = []
    original_ips = [] # Orignal IPs to check on NFS clients #

    for iface in ifaces:
        if "data" in iface["services"]:
            data_iface_names.append(iface["name"])
            original_ips.append(iface["address"])
        
    if len(original_ips) > 1:
        pure_ips = "|".join(original_ips)
    else:
        pure_ips = original_ips[0]
    
    # Get Interface info from s200 #
    ifaces_s200 = []
    test2 = pv3.Get_Single_Interface("testing-link", auth_token_s200, pv3.PB2_MGT)
    ifaces_s200.append(test2)
    data_iface_names_s200 = []

    for iface in ifaces_s200:
        if "data" in iface["services"]:
            data_iface_names_s200.append(iface["name"])

    # Get Replica links from legacy
    links = []
    test3 = pv3.Get_Single_Filesystem_Replica_Link("gxc_test", auth_token, pv3.PB1_MGT)
    links.append(test3)

    # Get NFS clients before swapping IPs #
    print("Getting list of active NFS clients to the pure...")
    print()
    clients = pv3.Get_NFS_Clients(auth_token, pv3.PB1_MGT, message=False)

    hosts = []
    for client in clients:
        host = client["name"]
        if "172.20.0." not in host:
            host = host.split(":")[0]
            hosts.append(host)

    inventory = {
        "all": {
            "hosts": {host: None for host in hosts}
        }
    }

    # Create temporary inventory file #
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        json.dump(inventory, f)
        f.flush()
        nfs_client_inventory = f.name

    # Create final snapshots prior to continuing swap #
    for fs in filesystems:
        if fs["promotion_status"] == "promoted":
            pv3.Post_Filesystem_Snapshot(fs["name"], auth_token, pv3.PB1_MGT, "pre-swap")

    print("Allowing 30 seconds for snapshots to take...")
    print()
    time.sleep(30)
    
    # For each legacy filesystem disable / demote #
    demote_payload = {
        "writable": False,
        "requested_promotion_state": "demoted"
    }
    for fs in filesystems:
        rc = pv3.Patch_Fs(fs["name"], auth_token, pv3.PB1_MGT, demote_payload, message="DEMOTED on legacy")
        while rc != 200:
            time.sleep(2.5) 
            print(f"\nTrying again with {fs['name']} until snapshot settles.\n")
            rc = pv3.Patch_Fs(fs["name"], auth_token, pv3.PB1_MGT, demote_payload, message="DEMOTED on legacy")
    
    # Patch Legacy IPs to s200 #
    for iface in ifaces:
        if iface["name"] in data_iface_names_s200:
            payload = { "address": iface["address"] }
            pv3.Patch_Interface(iface["name"], auth_token_s200, pv3.PB2_MGT, payload, message=f"s200:{iface['name']} assigned {iface['address']}")

    # Patch s200 IPs to Legacy #
    for iface in ifaces_s200:
        if iface["name"] in data_iface_names:
            payload = { "address": iface["address"] }
            pv3.Patch_Interface(iface["name"], auth_token, pv3.PB1_MGT, payload, message=f"legacy:{iface['name']} assigned {iface['address']}")
   
    # Disable replica links on Legacy #
    for link in links:
        pv3.Delete_Filesystem_Replica_Link(link["id"], auth_token, pv3.PB1_MGT)

    # For each s200 filesystem that is also in legacy enable / promote #
    for fs in filesystems:
        if fs["name"] in fs200_names:
            promote_payload = {
                "nfs": {
                    "v3_enabled": fs["nfs"]["v3_enabled"],
                    "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
                    "rules": fs["nfs"]["rules"]
                },
                "http": {
                    "enabled": fs["http"]["enabled"]
                },
                "writable": True,
                "requested_promotion_state": "promoted"
            }

            pv3.Patch_Fs(fs["name"], auth_token_s200, pv3.PB2_MGT, promote_payload, message="PROMOTED on s200")

    # Run Ansible playbook on nfs clients that need mounts fixed #
    print("Enter root password for ansible playbook.")
    subprocess.run(["ansible-playbook", "-i", f"{nfs_client_inventory}", "-e", f"pure_ips={pure_ips}", "--limit", "172.16.203.133", "-k", "remount-pure.yml"])
    
    # Clean up #
    os.remove(nfs_client_inventory)





