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


########################
### POST API Section ###
########################


#########################
### PATCH API Section ###
#########################


##########################
### DELETE API Section ###
##########################


### Main Function ###
def Main():
    print("TODO")

### Run Script ###
if __name__ == "__main__":
    Main()