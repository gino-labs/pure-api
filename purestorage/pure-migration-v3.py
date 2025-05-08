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
    else:
        return args.filesystems


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