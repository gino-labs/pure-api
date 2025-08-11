#!/usr/bin/env python3
import os
import json
import urllib3
import requests

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
    def REST_Request(self, method, url, message, payload=None):
        method = str(method).lower()
        if method == "get":
            response = requests.get(url, headers=self.auth_headers, verify=False)
        elif method == "post":
            response = requests.post(url, headers=self.auth_headers, json=payload, verify=False)
        elif method == "patch":
             response = requests.patch(url, headers=self.auth_headers, json=payload, verify=False)
        elif method == "delete":
            response = requests.delete(url, headers=self.auth_headers, verify=False)
        
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


    # Get api version used by blade
    def get_api_version(self, dumpjson=False):
        url = f"https://{self.mgt_ip}/api/api_version"
        msg = "API version"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]

    # Get single filesystem by name
    def get_single_filesystem(self, filesystem, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]
            
    # Get Filesystems
    def get_filesystems(self, dumpjson=False):
        url = self.baseurl + "file-systems"
        msg = "filesystems"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get single object store account by name
    def get_single_object_store_account(self, account, dumpjson=False):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]
        
    # Get object store accounts
    def get_object_store_accounts(self, dumpjson=False):
        url = self.baseurl + "object-store-accounts"
        msg = "object store accounts"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get single bucket by name
    def get_single_bucket(self, bucket, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]
        
    # Get buckets
    def get_buckets(self, dumpjson=False):
        url = self.baseurl + "buckets"
        msg = "buckets"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get single object store user by name
    def get_single_object_store_user(self, user, dumpjson=False):
        url = self.baseurl + f"object-store-users?names={user}"
        msg = f"object store user: {user}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]
        
    # Get object store users
    def get_object_store_users(self, dumpjson=False):
        url = self.baseurl + f"object-store-users"
        msg = f"object store users"
        data = self.REST_Request("get", url, msg, dumpjson=False)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get single object store access key by name
    def get_single_object_store_access_key(self, key, dumpjson=False):
        url = self.baseurl + f"object-store-access-keys?names={key}"
        msg = f"object store access key: {key}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]

    # Get object store access keys
    def get_object_store_access_keys(self, dumpjson=False):
        url = self.baseurl + f"object-store-access-keys"
        msg = "object store access keys"
        data = self.REST_Request("get", url, msg, dumpjson=False)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"][0]
        
    # Get single subnet by name
    def get_single_subnet(self, subnet, dumpjson=False):
        url = self.baseurl + f"subnets?names={subnet}"
        msg = f"subnet: {subnet}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]

    # Get subnets
    def get_subnets(self, dumpjson=False):
        url = self.baseurl + "subnets"
        msg = "subnets"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]

    # Get single network interface by name
    def get_single_interface(self, interface, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]
        
    # Get network interfaces
    def get_interfaces(self, dumpjson=False):
        url = self.baseurl + "network-interfaces"
        msg = "network interfaces"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]

    # Get single filesystem replica link by filesystem name
    def get_single_filesytem_replica_link(self, filesystem, dumpjson=False):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={filesystem}" 
        msg = f"filesystem replica link: {filesystem}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]

    # Get filesystem replica links
    def get_filesytem_replica_links(self, dumpjson=False):
        url = self.baseurl + "file-system-replica-links" 
        msg = "filesystem replica links"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get single filesystem snapshot by name or filesystem name
    def get_single_filesystem_snapshot(self, snapshot, dumpjson=False):
        url = self.baseurl + f"file-system-snapshots?names_or_owner_names={snapshot}"
        msg = f"filesystem snapshot: {snapshot}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"][0], indent=4))
            return data["items"][0]
        
    # Get filesystem snapshots
    def get_filesystem_snapshots(self, dumpjson=False):
        url = self.baseurl + f"file-system-snapshots"
        msg = f"filesystem snapshots"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get single snapshot policy and attached members
    def get_single_snapshot_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"policies?names={policy}"
        msg = f"filesystem snapshot policy: {policy}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data, indent=4))
            return data["items"]
        
    # Get snapshot polices
    def get_snapshot_policies(self, dumpjson=False):
        url = self.baseurl + "policies"
        msg = "filesystem snapshot policies"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
    # Get snapshot policies attached 
    def get_filesystems_attached_to_snapshot_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"file-systems/policies?policy_names={policy}"
        msg = f"attached snapshot policy: {policy}"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
       
    # Get connected NFS clients
    def get_nfs_clients(self, dumpjson=False):
        url = self.baseurl + "arrays/clients/performance"
        msg = "NFS clients"
        data = self.REST_Request("get", url, msg)

        if data is not None:
            if dumpjson:
                print(json.dumps(data["items"], indent=4))
            return data["items"]
        
        
    ########################
    ### POST API Section ###
    ########################


    # Post a filesystem (default NFS)
    def post_filesystem(self, filesystem, payload):
        url = self.baseurl + f"file-systems?names={filesystem}&default_exports=nfs"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("post", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]
        
    # Post an object store account
    def post_object_store_account(self, account, payload):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
        data = self.REST_Request("post", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]

    # Post a bucket
    def post_bucket(self, bucket, payload):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
        data = self.REST_Request("post", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]
        
    # Post an object store user
    def post_object_store_user(self, user):
        url = self.baseurl + f"object-store-users?names={user}&full_access=true"
        msg = f"object store user: {user}"
        data = self.REST_Request("post", url, msg)

        if data is not None:
            return data["items"][0]
        
    # Post an object store access key (Secret key shown once in response)
    def post_object_store_access_key(self, user, payload):
        url = self.baseurl + "object-store-access-keys"
        msg = f"object store access key: {user}"
        data = self.REST_Request("post", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]
        
    # Post a subnet
    def post_subnet(self, subnet, paylaod):
        url = self.baseurl + f"subnets?names={subnet}"
        msg = f"subnet: {subnet}"
        data = self.REST_Request("post", url, msg, payload=paylaod)

        if data is not None:
            return data["items"][0]

    # Post a network interface
    def post_interface(self, interface, payload):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("post", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]

    # Post a filesystem replica link #TODO TEST endpoint#
    def post_filesystem_replica_link(self, filesystem, payload):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={filesystem}"
        msg = f"filesystem replica link: {filesystem}"
        data = self.REST_Request("post", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]
        
    # Post a filesystem snapshot
    def post_filesystem_snapshot(self, filesystem, snapshot, replicate=True):
        if replicate:
            url = self.baseurl + f"file-system-snapshots?source_names={filesystem}&send=true"
        else:
            url = self.baseurl + f"file-system-snapshots?source_names={filesystem}"
        msg = f"filesytem snapshot: {snapshot} for {filesystem}"
        data = self.REST_Request("post", url, msg, payload={"suffix":snapshot})

        if data is not None:
            return data["items"][0]
        
    # Post snapshot scheduling policy to a filesystem
    def post_snapshot_policy_to_filesystem(self, policy, filesystem):
        url = self.baseurl + f"file-systems/policies?member_names={filesystem}&policy_names={policy}"
        msg = f"snapshot policy {policy} to {filesystem}"
        data = self.REST_Request("post", url, msg)

        if data is not None:
            return data["items"][0]


    #########################
    ### PATCH API Section ###
    #########################
        
        
    # Patch a filesystem
    def patch_filesystem(self, filesystem, payload):
        url = self.baseurl + f"file-systems?names={filesystem}"
        if payload["requested_promotion_state"] == "demoted":
            url = url + "&discard_non_snapshotted_data=true"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("patch", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]

    # Patch a network interface
    def patch_interface(self, interface, payload):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("patch", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]

    # Patch a snapshot
    def patch_filesystem_snapshot(self, snapshot, payload):
        url = self.baseurl + f"file-system-snapshots?names={snapshot}"
        if payload["destroyed"] == True:
            url = url + "&latest_replica=True"
        msg = f"filesystem snapshot: {snapshot}"
        data = self.REST_Request("patch", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]
        

    ##########################
    ### DELETE API Section ###
    ##########################
    

    # Delete a filesytem
    def delete_(self,):
        url = self.baseurl + f""
        msg = f""
        data = self.REST_Request("delete", url, msg)


    # Delete an object store user
    def delete_(self,):
        url = self.baseurl + f""
        msg = f""
        data = self.REST_Request("delete", url, msg)

    # Delete an object store access key
    def delete_(self,):
        url = self.baseurl + f""
        msg = f""
        data = self.REST_Request("delete", url, msg)

    # Delete a filesystem replica link
    def delete_(self,):
        url = self.baseurl + f""
        msg = f""
        data = self.REST_Request("delete", url, msg)

    # Delete a filesystem snapshot
    def delete_(self,):
        url = self.baseurl + f""
        msg = f""
        data = self.REST_Request("delete", url, msg)
        
