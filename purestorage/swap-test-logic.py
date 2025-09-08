#!/usr/bin/env python3
import json
import time
import purefb_log as pl
import purefb_api as pfa
import pure_migration_v3 as pv3


if __name__ == "__main__":
    #legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
    #s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

    def dump(data):
        print(json.dumps(data, indent=4))
        print()
        time.sleep(5)

    purelog = pl.PureLog()

    # Get auth tokens #
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)
    purelog.write_log("Auth tokens for legacy and s200 retrieved.")

    # Get List of Filesystems on Legacy #
    filesystems = pv3.Get_Filesystems(auth_token, pv3.PB1_MGT)
    purelog.write_log("Legacy filesystems retrieved")
    print(f"Legacy filesystems count before removing gxc: {len(filesystems)}")

    purelog.write_log(f"Legacy filesystems before with gxc...")
    # Remove gxc filesystems from list
    for fs in filesystems[:]:
        if "gxc" in fs.get("name", ""):
            filesystems.remove(fs)
    purelog.write_log("Legacy filesystems after without gxc...")
    print(f"Legacy filesystems count after removing gxc: {len(filesystems)}")

    # Get list of filesystems to Promote on S200
    filesystems200 = pv3.Get_Filesystems(auth_token_s200, pv3.PB2_MGT)
    purelog.write_log("S200 filesystems retreived")
    print(f"S200 filesystems count before removing gxc: {len(filesystems200)}")

    purelog.write_log("S200 filesystems before with gxc...")
    # Remove gxc filesystems from list
    for fs in filesystems200[:]:
        if "gxc" in fs.get("name", ""):
            filesystems200.remove(fs)
    purelog.write_log("S200 filesystems before without gxc...")
    print(f"Legacy filesystems count before removing gxc: {len(filesystems200)}")

    fs200_names = []
    for fs in filesystems200:
        fs200_names.append(fs["name"])
    purelog.write_log("S200 filesystems names list: ", jsondata=fs200_names)
    dump(fs200_names)

    # Get Interface info from legacy #
    ifaces = pv3.Get_Interfaces(auth_token, pv3.PB1_MGT)
    data_iface_names = []
    original_ips = [] # Orignal production IPs to check on NFS clients later #
    purelog.write_log("Legacy interfaces retrieved")
    print(len(ifaces))

    for iface in ifaces:
        if "data" in iface["services"]:
            data_iface_names.append(iface["name"])
            original_ips.append(iface["address"])
    purelog.write_log("Legacy data interface names list: ", jsondata=data_iface_names)
    purelog.write_log("Original data IPs of legacy FlashBlade used for Production: ", jsondata=original_ips)
    dump(data_iface_names)
    dump(original_ips)

    if len(original_ips) > 1:
        pure_ips = "|".join(original_ips)
    elif len(original_ips) == 1:
        pure_ips = original_ips[0]
    else:
        print("No data interfaces.")
        print()
    purelog.write_log(f"Pure IPs string passed to ansible play to grep then remount correct nfs mount: {pure_ips}")

    # Get Interface info from s200 #
    ifaces_s200 = pv3.Get_Interfaces(auth_token_s200, pv3.PB2_MGT)
    data_iface_names_s200 = []
    purelog.write_log("S200 interfaces retrieved")
    print(len(ifaces_s200))

    for iface in ifaces_s200:
        if "data" in iface["services"]:
            data_iface_names_s200.append(iface["name"])
    purelog.write_log("S200 data interface names list: ", jsondata=data_iface_names_s200)
    dump(data_iface_names_s200)

    # Get filesystem replica links
    links = pv3.Get_Filesystem_Replica_Links(auth_token, pv3.PB1_MGT)
    purelog.write_log("Replica links retrieved on Legacy")
    print(len(links))

    # Get NFS clients before swapping IPs #
    print("Getting list of active NFS clients to the pure...")
    print()
    clients = pv3.Get_NFS_Clients(auth_token, pv3.PB1_MGT, message=False)
    purelog.write_log("NFS Clients connected retrieved")

    hosts = []
    for client in clients:
        host = client["name"]
        if "172.20.0." not in host:
            host = host.split(":")[0]
            hosts.append(host)
    purelog.write_log("Updated list to exclude 172.20.0.X replication addresses: ", jsondata=hosts)
    dump(hosts)

    inventory = {
        "all": {
            "hosts": {host: None for host in hosts}
        }
    }
    purelog.write_log("Dynamic host inventory dictionary created for future ansible inventory")
    dump(inventory)

    # Simulate changes in order using logs
    purelog.write_log("Create temporary inventory file")

    purelog.write_log("Create final snapshots of promoted filesystems prior to swap followed by 30second wait timer for each filesystem.")

    purelog.write_log("On Legacy, for each filesystem Patch it to requested state demoted, writable false")

    purelog.write_log("Patch Legacy interfaces IPs to S200, only if name in S200 interface name list")

    purelog.write_log("Patch S200 interfaces IPs to Legacy, only if name in Legacy interface name list")

    purelog.write_log("Delete filesystem replica links on legacy. Unhealthy state if not done.")

    purelog.write_log("Patch requested Promotion state, writable True, protocols for each legacy filesystem name in S200 filesystem names list.")

    purelog.write_log("Enter root password and run ansible playbook")

    purelog.write_log(f"Ansible Cmd: ansible-playbook -i <temp-nfs-inventory> -e pure_ips={pure_ips} -k remount-pure.yml")

    purelog.write_log(f"Ansible task 1: Get list of systemd mount units using PureStorage")

    purelog.write_log(f"Ansible task 2: Restart the mount units")