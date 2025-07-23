#!/usr/bin/env python3
import os
import time
import json
import urllib3
import requests
from datetime import datetime

# Disabling Insecure Requests Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

################### ENVIRONMENT VARIABLES ###################  
PB1 = os.getenv("PB1")                                      #
PB2 = os.getenv("PB2")                                      #
PB1_MGT = os.getenv("PB1_MGT")                              #
PB2_MGT = os.getenv("PB2_MGT")                              #
LOCAL_IP = os.getenv("LOCAL_IP")                            #
API_TOKEN = os.getenv("API_TOKEN")                          #
API_TOKEN_S200 = os.getenv("API_TOKEN_S200")                #
MIGRATION_POLICY = os.getenv("MIGRATION_POLICY")            #
REPLICATION_CUTOFF = os.getenv("REPLICATION_CUTOFF")        #
#############################################################

class FlashBladeAPI():
    def __init__(self, data_ip, mgt_ip, api_token):
        self.data_ip = data_ip
        self.mgt_ip = mgt_ip
        self.api_token = api_token
        self.baseurl = f"https://{mgt_ip}/api/2.latest/"
        self.auth_token = self.Get_Session_Token()
        self.auth_headers = self.Set_Auth_Headers()

    # Get session token
    def Get_Session_Token(self):
        url = f"https://{self.mgt_ip}/api/login"

        headers = {
        "api-token": self.api_token,
        "Content-Type": "application/json"
    }
        response = requests.post(url, headers=headers, verify=False)

        if response.status_code == 200:
            return response.headers.get("x-auth-token")
        else:
            print(f"Login failed. Status Code: {response.status_code}\n{response.text}")
            print()
            return None
    
    # Set auth headers
    def Set_Auth_Headers(self):
        headers = {
            "x-auth-token": self.auth_token,
            "Content-Type": "application/json"
        }
        return headers
    
    # Make a api request
    def REST_Request(self, method, url, message):
        method = str(method).lower()
        if method == "get":
            response = requests.get(url, header=self.auth_headers, verify=False)
        elif method == "post":
            response = requests.post(url, header=self.auth_headers, verify=False)
        elif method == "patch":
             response = requests.patch(url, header=self.auth_headers, verify=False)
        elif method == "delete":
            response = requests.post(url, header=self.auth_headers, verify=False)
        
        if response.status_code == 200:
            print(f"{method.upper()} success for {message}")
            print()
            return response.json()
        else:
            print(f"Error Status Code: {response.status_code}\n{response.text}")
            print()
            return None
    
    #######################
    ### GET API Section ###
    #######################

    # Get single filesystem by name
    def get_single_filesystem(self, filesystem):
        url = self.baseurl + f"file-systems?names={filesystem}"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"][0]
            
    # Get Filesystems
    def get_filesystems(self):
        url = self.baseurl + "file-systems"
        msg = "filesystems"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"]
        
    # Get single object store account by name
    def get_single_object_store_account(self, account):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"][0]
        
    # Get object store accounts
    def get_object_store_accounts(self):
        url = self.baseurl + "object-store-accounts"
        msg = "object store accounts"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"]
        
    # Get single bucket by name
    def get_single_bucket(self, bucket):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"][0]
        
    # Get buckets
    def get_buckets(self):
        url = self.baseurl + "buckets"
        msg = "buckets"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"]
        
    # Get single object store user by name
    def get_single_object_store_user(self, user):
        url = self.baseurl + f"object-store-users?names={user}"
        msg = f"object store user: {user}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"][0]
        
    # Get object store users
    def get_object_store_users(self):
        url = self.baseurl + f"object-store-users"
        msg = f"object store users"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"]
        
    # Get single object store access key by name
    def get_single_object_store_access_key(self, key):
        url = self.baseurl + f"object-store-access-keys?names={key}"
        msg = f"object store access key: {key}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"][0]

    # Get object store access keys
    def get_object_store_access_keys(self):
        url = self.baseurl + f"object-store-access-keys"
        msg = f"object store access keys"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            return data["items"][0]
        
