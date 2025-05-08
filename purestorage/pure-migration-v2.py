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
PB1 = "pb1"                                        #
PB2 = "pb2"                                        #
PB1_MGT = "bazpureblade-mgt-vip"                   #
PB2_MGT = "azpureblade-vip"                        #
LOCAL_IP = "172.16.205.170"                        #
API_TOKEN = os.getenv("API_TOKEN")                 #
API_TOKEN_S200 = os.getenv("API_TOKEN_S200")       #
MIGRATION_POLICY = "blue_migration"                #
####################################################


# Parse CLI arguments of filesystem names
def Parse_FS_Args():
    script_name = os.path.basename(__file__)

    parser = argparse.ArgumentParser(
        usage=f"{script_name} FS1 [FS2 ...]",
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
    else:
        return args.filesystems


# Exchage API token for a session token
def Get_Session_Token(api_token, mgt_ip):
    login_url = f"https://{mgt_ip}/api/login"

    login_response = requests.post(
        login_url, headers={"api-token": api_token}, verify=False
    )

    if login_response.status_code == 200:
        return login_response.headers.get("x-auth-token")
    else:
        print(f"{login_response.status_code}\n{login_response.text}", file=sys.stderr)
        sys.exit(1)


# Make sure filesystem passed in exists
def Check_FS_Exists(filesystem, auth_token, mgt_ip=PB1_MGT):
    url_endpoint = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    response = requests.get(
        url_endpoint, headers={"x-auth-token": auth_token}, verify=False
    )

    if response.status_code == 200:
        return True
    else:
        print(f"Error: {response.status_code}, Filesystem '{filesystem}' doesn't exist")
        return False


# Add export rule to filesystem to include localhost
def Update_Export_Rule(filesystem, auth_token, mgt_ip=PB1_MGT, write_rule="ro", local_ip=LOCAL_IP):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {"x-auth-token": auth_token, "Content-Type": "application/json"}

    rule = f"{LOCAL_IP}({write_rule},no_root_squash)"

    update_data = {"nfs": {"v3_enabled": True, "v4_1_enabled": True, "add_rules": rule}}

    # Check if already exists
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        data = response.json()
        rules = data["items"][0]["nfs"]["rules"]
        if rule not in rules:
            response = requests.patch(
                url, headers=headers, json=update_data, verify=False
            )
            if response.status_code == 200:
                print(f"Updated with {rule}")
        else:
            print(f"Rule: {rule}, already exists")

            print(f"Patch Status Code: {response.status_code}")
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")


# Add Export Policy
def Update_Export_Policy(filesystem, auth_token, mgt_ip=PB2_MGT, policy=MIGRATION_POLICY):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    headers = {"x-auth-token": auth_token, "Content-Type": "application/json"}

    update_data = {"nfs": {"export_policy": {"name": policy}}}

    # Check if already exists
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        data = response.json()
        policy_check = data["items"][0]["nfs"]["export_policy"]["name"]
        if policy not in policy_check:
            response = requests.patch(
                url, headers=headers, json=update_data, verify=False
            )
            if response.status_code == 200:
                print(f"Updated with {rule}")
        else:
            print(f"Policy: {policy}, already exists")

            print(f"Patch Status Code: {response.status_code}")
    else:
        print(f"Error Status Code: {response.status_code}\n{response.text}")



# Get filesystem provision size in bytes
def Get_FS_Size(filesystem, auth_token, mgt_ip=PB1_MGT):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    response = requests.get(url, headers={"x-auth-token": auth_token}, verify=False)

    if response.status_code == 200:
        data = response.json()
        return data["items"][0]["provisioned"]
    else:
        print(f"Error: {response.status_code}")
        sys.exit()


# Delete filesystem with confirmation. Always Double Check before using this function.
def Delete_FS(filesystem, auth_token, mgt_ip=PB2_MGT):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"
    url2 = f"https://{mgt_ip}/api/2.latest/file-systems-exports?names={filesystem}"
    headers = {"x-auth-token": auth_token, "Content-Type": "application/json"}

    confirmation = (
        input(
            f"Are you sure you want to delete the filesystem '{filesystem}' on {mgt_ip}? (y/n): "
        )
        .strip()
        .lower()
    )

    if confirmation == "y":
        data_update = {
            "destroyed": True,
            "nfs": {"v3_enabled": False, "v4_1_enabled": False},
        }

        destroyed_response = requests.patch(
            url, headers=headers, json=data_update, verify=False
        )
        if destroyed_response.status_code != 200:
            print(
                f"Status Code Error: {destroyed_response.status_code}\n{destroyed_response.text}"
            )
            sys.exit(1)

        response = requests.delete(url, headers=headers, verify=False)
        print(f"Filesystem Status Code: {response.status_code}\n{response.text}")
        response = requests.delete(url2, headers=headers, verify=False)
        print(f"Exports Status Code: {response.status_code}\n{response.text}")
    else:
        print("Exiting Script...")
        sys.exit(1)


# POST new filesystem with json data payload
def Post_FS(filesystem, auth_token, size, policy=MIGRATION_POLICY, mgt_ip=PB2_MGT):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}&default_exports=nfs"

    headers = {"x-auth-token": auth_token, "Content-Type": "application/json"}

    check_response = requests.get(url, headers=headers, verify=False)

    if check_response.status_code == 200:
        return False

    # Filesystem Data to POST
    data = {
        "writable": True,
        "hard_limit_enabled": True,
        "nfs": {
            "v3_enabled": True,
            "v4_1_enabled": True,
            #'rules': '172.16.203.133(rw,no_root_squash)',
            "export_policy": {"name": policy},
        },
        "smb": {
            "enabled": False,
            "client_policy": {"name": ""},
            "share_policy": {"name": ""},
        },
        "provisioned": size,
    }

    response = requests.post(url, headers=headers, json=data, verify=False)

    if response.status_code == 200:
        print(f"Filesystem POST: {filesystem}")
        return True
    else:
        print(f"Error {response.status_code}: {response.text}")
        return False


# Make directory and mount
def Mkdir_Mount_NFS(filesystem, src_ip=PB1, dest_ip=PB2):
    os.makedirs(f"/mnt/pure_migration/{filesystem}_source", exist_ok=True)
    os.makedirs(f"/mnt/pure_migration/{filesystem}_migration", exist_ok=True)

    if (
        subprocess.run(
            ["mountpoint", "-q", f"/mnt/pure_migration/{filesystem}_source"]
        ).returncode
        == 1
    ):
        subprocess.run(
            [
                "mount",
                "-t",
                "nfs",
                f"{src_ip}:/{filesystem}",
                f"/mnt/pure_migration/{filesystem}_source",
            ]
        )
    else:
        print("Already Mounted.")

    if (
        subprocess.run(
            ["mountpoint", "-q", f"/mnt/pure_migration/{filesystem}_migration"]
        ).returncode
        == 1
    ):
        subprocess.run(
            [
                "mount",
                "-t",
                "nfs",
                f"{dest_ip}:/{filesystem}",
                f"/mnt/pure_migration/{filesystem}_migration",
            ]
        )
    else:
        print("Already Mounted.")


# Unmount and remove directory
def Rmdir_Umount_NFS(filesystem, rmdir=True):
    subprocess.run(["umount", "-t", "nfs", f"/mnt/pure_migration/{filesystem}_source"])
    subprocess.run(
        ["umount", "-t", "nfs", f"/mnt/pure_migration/{filesystem}_migration"]
    )

    time.sleep(1)
    if rmdir:
        os.rmdir(f"/mnt/pure_migration/{filesystem}_source")
        os.rmdir(f"/mnt/pure_migration/{filesystem}_migration")
    else:
        print("Skipping Directory Removal.")

# Migrate with pcopy and rsync
def Pcopy_Rsync(filesystem, pcopy=True, rsync=True):
    src = f"/mnt/pure_migration/{filesystem}_source/"
    dest = f"/mnt/pure_migration/{filesystem}_migration"

    print(f"Migrating Data from {src} to {dest}")
    time.sleep(1)
    
    if pcopy:
        print(f"\nBegin Pcopying {filesystem}...")
        time.sleep(1)
        subprocess.run(["pcopy", "-pr", "--sparse=always", src + "/.", dest])
    else:
        print(f"Skipping pcopy for {filesystem}...")
    
    if rsync:
        print(f"\nBegin Rsyncing {filesystem}...")
        time.sleep(1)
        subprocess.run(
            ["rsync", "-havHS", "--progress", "--exclude", ".snapshot/", src, dest]
        )
    else:
        print(f"Skipping rsync for {filesystem}...")


# Calculate difference in bytes between two mounts
def Get_FS_Virtual_Size(filesystem, auth_token, mgt_ip):
    url = f"https://{mgt_ip}/api/2.latest/file-systems?names={filesystem}"

    response = requests.get(url, headers={"x-auth-token": auth_token}, verify=False)

    if response.status_code == 200:
        data = response.json()
        virt_size = data["items"][0]["space"]["virtual"]
        return virt_size 
    
    

# Write to migration log as filesystems complete
def Write_Migration_Log(filesystem, failure=False, log_file="pure_migration.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if failure:
        with open(log_file, "a") as log:
            log.write(f"- `{filesystem}` failed to rsync [{timestamp}]\n")
    else:
        with open(log_file, "a") as log:
            log.write(f"- `{filesystem}` rsynced to s200 [{timestamp}]\n")
    

#######################
#### MAIN Function ####
#######################


def Main():
    # Parse arguments
    filesystems = Parse_FS_Args()

    # Loop through one or more filesystems passed
    for fs in filesystems:
        # Get session tokens
        auth_token = Get_Session_Token(API_TOKEN, PB1_MGT)
        auth_token_s200 = Get_Session_Token(API_TOKEN_S200, PB2_MGT)
        if Check_FS_Exists(fs, auth_token):
            print(f"Filesystem does exist: {fs}\nContinuing with script...")
            time.sleep(1)
            # Get filesystem size
            size = Get_FS_Size(fs, auth_token)
            # Update export rule to include local host
            Update_Export_Rule(fs, auth_token)
            # Create new filesystem on S200
            if not Post_FS(fs, auth_token_s200, size):
                print(f"{fs} exists on {PB2_MGT}")
#                continue
            Update_Export_Policy(fs, auth_token_s200)
            # Run mkdir and mount
            try:
                Mkdir_Mount_NFS(fs)
                time.sleep(2)
                # Run pcopy and rsync
                Pcopy_Rsync(fs, pcopy=False)
                time.sleep(2)
            except Exception as e:
                print(f"Error occurred: {e}")
                Rmdir_Umount_NFS(fs)
            if len(filesystems) < 2:
                umount_end = (
                    input(
                        f"Would you like to umount {fs} from both source and destination? (y/n): "
                    )
                    .strip()
                    .lower()
                )
                if umount_end == "y":
                    Rmdir_Umount_NFS(fs, rmdir=False)
                else:
                    print(f"{fs} was left mounted.")
            else:
                print(f"Unmounting {fs}")
                Rmdir_Umount_NFS(fs, rmdir=False)
                time.sleep(2)
        
            # Writing Migration log to pure_migration.log
            Write_Migration_Log(fs)
        else:
            print(
                f"This filesystem does not exist: {fs}, moving on to next filesystem."
            )
            Write_Migration_Log(fs, failure=True)
            time.sleep(2)


### Run Script ###
if __name__ == "__main__":
    Main()
