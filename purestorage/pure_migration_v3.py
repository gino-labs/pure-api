#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib3
import requests
import argparse
import subprocess
from datetime import datetime

# Disabling Insecure Requests Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

################### GLOBAL VARIABLES ###################  
PB1 = os.getenv("PB1")                                 #
PB2 = os.getenv("PB2")                                 #
PB1_MGT = os.getenv("PB1_MGT")                         # 
PB2_MGT = os.getenv("PB2_MGT")                         #
LOCAL_IP = os.getenv("LOCAL_IP")                       #
API_TOKEN = os.getenv("API_TOKEN")                     #
API_TOKEN_S200 = os.getenv("API_TOKEN_S200")           #
MIGRATION_POLICY = os.getenv("MIGRATION_POLICY")       #
REPLICATION_CUTOFF = os.getenv("REPLICATION_CUTOFF")   #
########################################################

#######################
### Non-API Section ###
#######################

# Parse CLI arguments of filesystem names
def Parse_FS_Args():
    parser = argparse.ArgumentParser(
        description="Python Script to migrate filesystems using pcopy and rsync",
    )

    parser.add_argument("filesystems", nargs="*", help="One or more filesystem names")
    parser.add_argument("--file", help="Path to a filesystem")

    return parser.parse_args()

# Make directory for mounting
def Mkdir2(filesystem):
    os.makedirs(f"/mnt/pure_migration/{filesystem}_source", exist_ok=True)
    os.makedirs(f"/mnt/pure_migration/{filesystem}_destination", exist_ok=True)

# Mount Filesystem to directory mountpoint
def Mount2(filesystem, src_ip=PB1, dest_ip=PB2):
    src_path = f"/mnt/pure_migration/{filesystem}_source/"
    src_export = f"{src_ip}:/{filesystem}"
    dest_path = f"/mnt/pure_migration/{filesystem}_destination/"
    dest_export = f"{dest_ip}:/{filesystem}"

    if subprocess.run(["mountpoint", "-q", src_path]).returncode == 0:
        print(f"{src_path} : Already Mounted.")
        print()
    else:
        subprocess.run(
            ["mount", "-t", "nfs", src_export, src_path]
        )

    if subprocess.run(["mountpoint", "-q", dest_path]).returncode == 0:
        print(f"{dest_path} : Already Mounted.")
        print()
    else:
        subprocess.run(
            ["mount", "-t", "nfs", dest_export, dest_path]
        )

# Unmount nfs filesystems
def Unmount2(filesystem):
    src_path = f"/mnt/pure_migration/{filesystem}_source/"
    dest_path = f"/mnt/pure_migration/{filesystem}_destination/"

    if subprocess.run(["mountpoint", "-q", src_path]).returncode == 0:
        subprocess.run(["umount", src_path])
    else:
        print(f"{src_path} is not a mountpoint")
        print()

    if subprocess.run(["mountpoint", "-q", dest_path]).returncode == 0:
        subprocess.run(["umount", dest_path])
    else:
        print(f"{dest_path} is not a mountpoint")
        print()

# Remove directories used for mountpoints
def Rmdir2(filesystem):
    src_path = f"/mnt/pure_migration/{filesystem}_source/"
    dest_path = f"/mnt/pure_migration/{filesystem}_destination/"
    
    if os.path.isdir(src_path):
        os.rmdir(src_path)
    else: 
        print(f"No directory {src_path} : Doing nothing.")
        print()

    if os.path.isdir(dest_path):
        os.rmdir(dest_path)
    else: 
        print(f"No directory {dest_path} : Doing nothing.")
        print()

# Pcopy from source to destination points
def Pcopy(filesystem, sparse=False, verbose=False):
    src_path = f"/mnt/pure_migration/{filesystem}_source/"
    dest_path = f"/mnt/pure_migration/{filesystem}_destination/"

    # Verify if mounted first as a double check
    src_rc = subprocess.run(["mountpoint", "-q", src_path]).returncode
    dest_rc = subprocess.run(["mountpoint", "-q", src_path]).returncode

    if (src_rc == 0) and (dest_rc == 0):
        print("Starting pcopy...")
        print()
        if sparse and verbose:
            subprocess.run(["pcopy", "-prv", "--sparse=always", src_path, dest_path])
        elif sparse:
            subprocess.run(["pcopy", "-pr", "--sparse=always", src_path, dest_path])
        elif verbose:
            subprocess.run(["pcopy", "-prv", src_path, dest_path])
        else:
            subprocess.run(["pcopy", "-pr", src_path, dest_path])
    else:
        if src_rc != 0:
            print(f"{src_path} isn't mounted, skipping pcopy.")
        if dest_rc != 0:
            print(f"{dest_path} isn't mounted, skipping pcopy.")
        print()

# Rsync from source to destination points
def Rsync(filesystem, verbose=False, sparse=False):
    src_path = f"/mnt/pure_migration/{filesystem}_source/"
    dest_path = f"/mnt/pure_migration/{filesystem}_destination/"

    # Verify if mounted first as a double check
    src_rc = subprocess.run(["mountpoint", "-q", src_path]).returncode
    dest_rc = subprocess.run(["mountpoint", "-q", src_path]).returncode

    if (src_rc == 0) and (dest_rc == 0):
        print("Starting rsync...")
        print()
        if sparse and verbose:
            subprocess.run(["rsync", "-havH", "--sparse", "--progress", "--exclude", ".snapshot/", "--exclude", "*/.cache", src_path, dest_path])
        elif verbose:
            subprocess.run(["rsync", "-havH", "--progress", "--exclude", ".snapshot/", "--exclude", "*/.cache", src_path, dest_path])
        elif sparse:
            subprocess.run(["rsync", "-havH", "--sparse", "--exclude", ".snapshot/", "--exclude", "*/.cache", src_path, dest_path])
        else:
            subprocess.run(["rsync", "-havH", "--exclude", ".snapshot/", "--exclude", "*/.cache", src_path, dest_path])
    else:
        if src_rc != 0:
            print(f"{src_path} isn't mounted, skipping rsync.")
        if dest_rc != 0:
            print(f"{dest_path} isn't mounted, skipping rsync.")
        print()

# Write to migration log
def Write_Migration_Log(filesystem, passed=True, log_file="/mnt/pure_migration/pure_migration.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if passed:
        with open(log_file, "a") as log:
            log.write(f"- `{filesystem}` : successfully copied [{timestamp}]\n")
    else:
        with open(log_file, "a") as log:
            log.write(f"- `{filesystem}` : failed to copy [{timestamp}]\n")

# Write message to log
def Write_Message_Log(message, log_file="/mnt/pure_migration/pure_migration.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as log:
        log.write(f"{timestamp} - {message}")

# Write Keys + Users related to store accounts for buckets
def Save_Key_Info(user, access_key, secret_key, fb):

    data = {
        "flashblade": fb,
        "user": user,
        "access_key": access_key,
        "secret_key": secret_key,
    }

    with open("keys.jsonl", "a") as keyfile:
        json.dump(data, keyfile)
        keyfile.write("\n")

#######################
### GET API Section ###
#######################

# Get API versions
def Get_API_Versions(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/api_version"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(response.text)
        print()
    else:
        print(f"Error status code: {response.status_code}\n{response.text}")
        print()


# Retrieve session token using POST request with api token. Only excpetion to sections.
def Get_Session_Token(api_token, mgt_ip, message=True):
    url = f"https://{mgt_ip}/api/login"

    headers = {
        "api-token": api_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, verify=False)

    if response.status_code == 200:
        if message:
            print()
        return response.headers.get("x-auth-token")
    else:
        print(f"Login failed. Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# GET filesystem as a json object
def Get_Single_Filesystem(filesystem, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for filesystem: {filesystem}")
        print()
        data = response.json()
        
        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get Filesystems json (List) TODO
def Get_Filesystems(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-systems"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print("GET success for filesystems.")
        print()

        data = response.json()
        items = data["items"]

        return items   
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None     

# Get object store accounts json (List)
def Get_Obj_Accounts(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-accounts"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print("GET success for object store accounts list.")
        print()

        data = response.json()
        items = data["items"]

        return items
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get single object store account by name
def Get_Single_Obj_Account(account, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-accounts?names={account}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for object store account: {account}.")
        print()

        data = response.json()

        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get object store bucket json
def Get_Buckets(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/buckets"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print("GET success for buckets.")
        print()

        data = response.json()
        items = data["items"]

        return items
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get single bucket json object info
def Get_Single_Bucket(bucket, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/buckets?names={bucket}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for object store account: {bucket}.")
        print()

        data = response.json()

        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
         
# Get object store access keys json (name + user name)
def Get_Obj_Access_Keys(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-access-keys"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print("GET object store access keys success.")
        print()

        data = response.json()
        items = data["items"]

        return items
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get existing account access key
def Get_Single_Obj_Access_Key(key_name, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/2.latest/object-store-access-keys?names={key_name}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for object store access key: {key_name}.")
        print()

        data = response.json()

        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get list of object store users
def Get_Obj_Users(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-users"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for object users.")
        print()

        data = response.json()
        return data["items"]
    
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get single object store user
def Get_Single_Obj_User(user, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-users?names={user}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for object user: {user}")
        print()
        
        data = response.json()
        return data["items"][0]
    
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get subnets info
def Get_Subnets(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/subnets"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for subnets.")
        print()
        data = response.json()
        return data["items"]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get single subnet info
def Get_Single_Subnet(subnet, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/subnets?names={subnet}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for subnet: {subnet}")
        print()
        data = response.json()
        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get interfaces
def Get_Interfaces(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/network-interfaces"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for interfaces")
        print()
        data = response.json()
        return data["items"]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get single interface
def Get_Single_Interface(interface, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/network-interfaces?names={interface}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for interface: {interface}")
        print()
        data = response.json()
        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get filesystem replica links
def Get_Filesystem_Replica_Links(auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-system-replica-links"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for filesystem replica links.")
        print()
        data = response.json()
        return data["items"]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get single replica link by name    
def Get_Single_Filesystem_Replica_Link(local_fs, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-system-replica-links?local_file_system_names={local_fs}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for filesystem replica link: {local_fs}.")
        print()
        data = response.json()
        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Get list of NFS clients
def Get_NFS_Clients(auth_token, mgt_ip, message=True):
    url = f"https://{mgt_ip}/api/2.latest/arrays/clients/performance"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        if message:
            print(f"GET success for NFS clients.")
            print()
        data = response.json()
        return data["items"]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Get a single snapshot by name
def Get_Single_Filesystem_Snapshot(snapshot, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-system-snapshots?names_or_owner_names={snapshot}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"GET success for snapshot: {snapshot}.")
        print()
        data = response.json()
        return data["items"][0]
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    

########################
### POST API Section ###
########################

# Create filesystem with a json payload
def Post_Filesystem(auth_token, mgt_ip, name, payload, migration_policy=True):
    # Add migration policy on top of existing filesystem
    if migration_policy:
        payload["nfs"]["export_policy"]["name"] = MIGRATION_POLICY

    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={name}&default_exports=nfs"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for NFS fileystem: {name}")
        print()
        return response.status_code
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None



# Create a new NFS filesystem
def Post_Fs_Nfs(filesystem, auth_token, mgt_ip, size, rules=None, export_policy=None, write=True, hard_limit=True):
    if (rules is None) and (export_policy is None):
        print("You didn't pass in any rules or export policies. Exiting...")
        print()
        return None
    
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}&default_exports=nfs"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    payload = {
        "writable": write,
        "hard_limit_enabled": hard_limit,
        "provisioned": size,
        "nfs" : {
            "v3_enabled": True,
            "v4_1_enabled": True,
        }
    }

    if rules is not None:
        payload["nfs"]["rules"] = rules
    if export_policy is not None:
        payload["nfs"]["export_policy"] = {"name": export_policy}

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for NFS fileystem: {filesystem}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Create a new SMB filesystem
def Post_Fs_Smb(filesystem, auth_token, mgt_ip, size, client_policy=None, share_policy=None, write=True, hard_limit=True):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}&default_exports=smb"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    payload = {
        "writable": write,
        "hard_limit_enabled": hard_limit,
        "provisioned": size,
        "smb" : {
            "enabled": True,
        }
    }

    if client_policy is not None:
        payload["smb"]["client_policy"] = {"name": client_policy}
    if share_policy is not None:
        payload["smb"]["share_policy"] = {"name": share_policy}
    if (client_policy is None) and (share_policy is None):
        print("You didn't specify client or share policy. Using defaults...")
        print()
    
    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for SMB fileystem: {filesystem}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None        
    
# Create object store account
def Post_Obj_Account(auth_token, mgt_ip, name, payload):
    url = f"https://{mgt_ip}/api/2.latest/object-store-accounts?names={name}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for object store account: {name}")
        print()    
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None        
    
# Create bucket
def Post_Bucket(auth_token, mgt_ip, name, payload):
    url = f"https://{mgt_ip}/api/2.latest/buckets?names={name}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for object store account: {name}")
        print()    
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Create object store user # Removed payload
def Post_Obj_User(auth_token, mgt_ip, user):
    url = f"https://{mgt_ip}/api/2.latest/object-store-users?names={user}&full_access=true"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"POST success for object store user: {user}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Post a temporary object store user
def Post_Temp_Obj_User(auth_token, mgt_ip, acct_name):
    tempuser = f"{acct_name}/tempuser"
    
    url = f"https://{mgt_ip}/api/2.latest/object-store-users?names={tempuser}&full_access=true"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    payload = {
        "name": tempuser,
        "account": {
            "name": acct_name
        }
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for temporary object store user: {tempuser}")
        print()
        return tempuser
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None


# Create access key (TEST can I save secret key?)
def Post_Access_Key(auth_token, mgt_ip, payload):
    url = f"https://{mgt_ip}/api/2.latest/object-store-access-keys"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for access key")
        print()   

        data = response.json()

        return data["items"][0]

    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Create a filesystem replica link
def Post_Filesystem_Replica_Link(fs_name, remote_array, auth_token, mgt_ip, payload):
    url = f"https://{mgt_ip}/api/2.latest/file-system-replica-links?names={fs_name}&local_file_system_names={fs_name}&remote_file_system_names={fs_name}&remote_names={remote_array}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for replica link to {fs_name}")
        print()   

        data = response.json()

        return data["items"][0]

    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Create a filesystem snapshot
def Post_Filesystem_Snapshot(fs, auth_token, mgt_ip, suffix, replicate=True):
    if replicate:
        url = f"https://{mgt_ip}/api/2.latest/file-system-snapshots?source_names={fs}&send=true"
    else:
        url = f"https://{mgt_ip}/api/2.latest/file-system-snapshots?source_names={fs}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json={"suffix": suffix}, verify=False)

    if response.status_code == 200:
        print(f"POST success for snapshot {suffix} to {fs}")
        print()   

        data = response.json()

        return data["items"][0]

    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None


# Add subnet with json payload to pureblade endpoint
def Post_Subnet(subnet, auth_token, mgt_ip, payload):
    url = f"https://{mgt_ip}/api/2.latest/subnets?names={subnet}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for subnet: {subnet}")
        print()
        return 200
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Add network interface tied to a subnet
def Post_Interface(interface, auth_token, mgt_ip, payload):
    url = f"https://{mgt_ip}/api/2.latest/network-interfaces?names={interface}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"POST success for interface: {interface}")
        print()
        return 200
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None



#########################
### PATCH API Section ###
#########################

# Update filesystem with a json payload passed into function
def Patch_Fs(filesystem, auth_token, mgt_ip, payload, message=None):
    if payload["requested_promotion_state"] == "demoted":
        url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}&discard_non_snapshotted_data=true"
    else:
        url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json=payload, verify=False)
    
    if response.status_code == 200:
        if message:
            print(f"PATCH success for filesystem: {filesystem} ({str(message)})")
        else:
            print(f"PATCH success for filesystem: {filesystem}")
        print()
        return 200
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Add export rule for localhost to mount if it doesn't exist
def Patch_Export_Rule(filesystem, auth_token, mgt_ip, local_ip=LOCAL_IP):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    # Check if rule already exists
    fs = Get_Single_Filesystem(filesystem, auth_token, mgt_ip)

    if fs is None:
        print(f"Filesystem {fs} doesn't exist. Skipping PATCH...")
        print()
        return None
    
    rule = f"{local_ip}(ro,no_root_squash)"
    rules = fs["nfs"]["rules"]

    if rule in rules:
        print(f"Rule: {rule} already in rules.")
        print()
        return None
    
    payload = {
        "nfs": {
            "v3_enabled": True,
            "v4_1_enabled": True,
            "add_rules": rule
        }
    }

    response = requests.patch(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        print(f"PATCH success for export rule: {rule}")
        print()
        return 200
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Update a network interface
def Patch_Interface(iface, auth_token, mgt_ip, payload, message=None):
    url = f"https://{mgt_ip}/api/2.latest/network-interfaces?names={iface}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        if message:
            print(f"PATCH success for network interface: {iface} ({str(message)})")
        else:
            print(f"PATCH success for network interface: {iface}")
        print()
        return 200
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Update a snapshot
def Patch_Filesystem_Snapshot(snapshot, auth_token, mgt_ip, payload, destroy=False, message=None):
    if destroy:
        url = f"https://{mgt_ip}/api/2.latest/file-system-snapshots?names={snapshot}&latest_replica=True"
    else:
        url = f"https://{mgt_ip}/api/2.latest/file-system-snapshots?names={snapshot}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        if message:
            print(f"PATCH success for snapshot: {snapshot} ({str(message)})")
        else:
            print(f"PATCH success for snapshot: {snapshot}")
        print()
        return 200
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None


##########################
### DELETE API Section ###
##########################

# Delete a filesystem. Note: Will need to mark a filesystem as 'destroyed' first to work. Use Patch_FS()
def Delete_Fs(filesystem, auth_token, mgt_ip, confirm=True):
    if confirm:
        confirmation = input(f"Are you sure you want to delete '{filesystem} from {mgt_ip}'? (y/n) ").strip().lower()

        if confirmation == 'y':
            print(f"Proceeding to delete {filesystem} in 5 seconds...")
            time.sleep(5.5)
        else:
            print(f"Skipping Deletion...")
            print()
            return None
    
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"Filesystem {filesystem} was deleted from {mgt_ip}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Delete an Object Store Access Key 
def Delete_Access_Key(name, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-access-keys?names={name}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"DELETE success for access key: {name}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None


# Delete and Object Store User
def Delete_Obj_User(name, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/object-store-users?names={name}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"DELETE success for object store user: {name}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# Delete a filesystem replica link
def Delete_Filesystem_Replica_Link(local_fs, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-system-replica-links?ids={local_fs}&cancel_in_progress_transfers=true"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"DELETE success for filesystem replica link with id: {local_fs}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

# Delete a snapshot
def Delete_Filesystem_Snapshot(snapshot, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-system-snapshots?names={snapshot}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 200:
        print(f"DELETE success for filesystem snapshot: {snapshot}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

#####################
### Main Function ###
#####################

def Main():
    # Parse CLI Arguments
    args = Parse_FS_Args()
    # Add logic to use parser namespace (filesystems, file)
    print("Offloading tasks to separate scripts to import.")
    print()

### Run Script ###
if __name__ == "__main__":
    Main()
