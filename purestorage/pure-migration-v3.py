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

################# GLOBAL VARIABLES #################
PB1 = ""                                           #
PB2 = ""                                           #
PB1_MGT = ""                                       #
PB2_MGT = ""                                       #
LOCAL_IP = ""                                      #
API_TOKEN = ""                                     #
API_TOKEN_S200 = ""                                #
MIGRATION_POLICY = ""                              #
####################################################

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

    args = parser.parse_args()

    if args.file:
        cwd = os.getcwd()
        fs_file = f"{cwd}/{args.file}"
        if os.path.isfile(fs_file):
            with open(fs_file, "r") as f:
                lines = f.read().splitlines()
                return lines
        else:
            print(f"{fs_file} is not a file.")
            print()
    else:
        return args.filesystems

# Make directory for mounting
def Mkdir2(filesystem):
    os.makedirs(f"/mnt/pure_migration/{filesystem}_source", exist_ok=True)
    os.makedirs(f"/mnt/pure_migration/{filesystem}_migration", exist_ok=True)

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
            subprocess.run(["rsync", "-havH", "--sparse", "--progress", src_path, dest_path])
        elif verbose:
            subprocess.run(["rsync", "-havH", "--progress", src_path, dest_path])
        elif sparse:
            subprocess.run(["rsync", "-havH", "--sparse", src_path, dest_path])
        else:
            subprocess.run(["rsync", "-havH", src_path, dest_path])
    else:
        if src_rc != 0:
            print(f"{src_path} isn't mounted, skipping rsync.")
        if dest_rc != 0:
            print(f"{dest_path} isn't mounted, skipping rsync.")
        print()

# Write to migration log
def Write_Migration_Log(filesystem, passed=True, log_file="pure_migration.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if passed:
        with open(log_file, "a") as log:
            log.write(f"- `{filesystem}` : successfully copied [{timestamp}]\n")
    else:
        with open(log_file, "a") as log:
            log.write(f"- `{filesystem}` : failed to copy [{timestamp}]\n")


#######################
### GET API Section ###
#######################

# Retrieve session token using POST request with api token. Only excpetion to sections.
def Get_Session_Token(api_token, mgt_ip):
    url = f"https://{mgt_ip}/api/login"

    headers = {
        "api-token": api_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, verify=False)

    if response.status_code == 200:
        print()
        return response.headers.get("x-auth-token")
    else:
        print(f"Login failed. Status Code: {response.status_code}\n{response.text}")
        print()
        return None
    
# GET filesystem as a json object
def Get_Fs_Json(filesystem, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print()
        data = response.json()
        fs_data = data["items"][0]
        return fs_data
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None


########################
### POST API Section ###
########################

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
        print(f"Successful NFS fileystem creation: {filesystem}")
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
        print(f"Successful SMB fileystem creation: {filesystem}")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None        
    

#########################
### PATCH API Section ###
#########################

# Add filesystem with a json payload passed into function
def Patch_Fs(filesystem, auth_token, mgt_ip, payload):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {
        "x-auth-token": auth_token,
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json=payload, verify=False)
    
    if response.status_code == 200:
        print(f"Update Successful.")
        print()
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
        print(f"Filesystem {filesystem} was deleted from {mgt_ip}.")
        print()
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")
        print()
        return None

#####################
### Main Function ###
#####################

def Main():
    print("TODO")

### Run Script ###
if __name__ == "__main__":
    Main()
