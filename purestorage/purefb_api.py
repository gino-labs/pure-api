#!/usr/bin/env python3
import os
import sys
import json
import urllib3
import requests
import purefb_log as pfl

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

class FlashBladeAPI:
    def __init__(self, data_ip, mgt_ip, api_token):
        try:
            self.name = mgt_ip.split("-")[0]
            self.data_ip = data_ip
            self.mgt_ip = mgt_ip
            self.api_token = api_token
            self.baseurl = f"https://{mgt_ip}/api/2.latest/"
            self.auth_token = self.Get_Session_Token()
            self.auth_headers = self.Set_Auth_Headers()
            self.logger = pfl.PureLog()
        except requests.RequestException as e:
            e_msg = f"\nError RequestException occured. Please check your environment variables are correctly set."
            print(f"{e_msg}")
            print()
            sys.exit(1)

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
            msg = f"{method.upper()} success for {message}"
            self.logger.write_log(msg, show_output=True)
            if method == "delete":
                return {"status_code": response.status_code, "text": response.text}
            else:
                return response.json()
        else:
            err_json = json.loads(response.text)
            err_code = f"Error Status Code: {response.status_code}"
            self.logger.write_log(err_code)
            self.logger.write_log(response.text)
            print(err_code)
            print(response.text)
            print()
            return None

    # Parse json data or rest request items
    def Parse_Data(self, data, dump=False):
        def log_print(msg, show_data=None, debug=dump):
            if debug:
                if show_data is not None:
                    self.logger.write_log(msg, jsondata=show_data)
                    print(msg)
                    print(json.dumps(show_data, indent=4))
                    print()
                else:
                    self.logger.write_log(msg)
                    print(msg)
                    print()

        if data is not None:
            try:
                if len(data["items"]) == 1:
                    log_print("DEBUG: See parsed data", show_data=data["items"][0])
                    return data["items"][0]
                log_print("DEBUG: See parsed data", show_data=data["items"])
                return data["items"]
            except Exception as e:
                log_print(f"Exception has occured:\n {e}", debug=True)
                log_print("Returning full unparsed json data insead", debug=True)
                if dump:
                    log_print("Json output for data", show_data=data, debug=True)
                return data
        else:
            log_print("Data returned is None. Please check endpoint or call.")

    # Helper function to return a csv string or single string
    def to_csv(self, value):
        if isinstance(value, str):
            return value
        return ",".join(value)
        

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
                print(json.dumps(data, indent=4))
            return data["versions"]
            
    # Get Filesystems
    def get_filesystems(self, filesystems=None, dumpjson=False):
        if filesystems is not None:
            fs_list = self.to_csv(filesystems)
            url = self.baseurl + f"file-systems?names={fs_list}"
            msg = f"filesystems: {filesystems}"      
        else:
            url = self.baseurl + "file-systems"
            msg = "filesystems"
            
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get object store accounts
    def get_object_store_accounts(self, accounts=None, dumpjson=False):
        if accounts is not None:
            acct_list = self.to_csv(accounts)
            url = self.baseurl + f"object-store-accounts?names={acct_list}"
            msg = f"object store accounts: {acct_list}"
        else:
            url = self.baseurl + "object-store-accounts"
            msg = "object store accounts"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get buckets
    def get_buckets(self, buckets=None, dumpjson=False):
        if buckets is not None:
            buck_list = self.to_csv(buckets)
            url = self.baseurl + f"buckets?names={buck_list}"
            msg = f"buckets: {buck_list}"
        else:
            url = self.baseurl + "buckets"
            msg = "buckets"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get bucket replica links
    def get_bucket_replia_links(self, buckets=None, dumpjson=False):
        if buckets is not None:
            buck_list = self.to_csv(buckets)
            url = self.baseurl + f"bucket-replica-links?local_bucket_names={buck_list}"
            msg = f"bucket replica links: {buck_list}"
        else:
            url = self.baseurl + f"bucket-replica-links"
            msg = f"bucket replica links"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get object store users
    def get_object_store_users(self, users=None, dumpjson=False):
        if users is not None:
            user_list = self.to_csv(users)
            url = self.baseurl + f"object-store-users?names={user_list}"
            msg = f"object store users: {users}"
        else:
            url = self.baseurl + f"object-store-users"
            msg = f"object store users"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Get object store access keys
    def get_object_store_access_keys(self, keys=None, dumpjson=False):
        if keys is not None:
            key_list = self.to_csv(keys)
            url = self.baseurl + f"object-store-access-keys?names={key_list}"
            msg = f"object store access keys: {key_list}"
        else:
            url = self.baseurl + f"object-store-access-keys"
            msg = "object store access keys"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get object store remote credentials
    def get_object_store_remote_credentials(self, credentials=None, dumpjson=False):
        if credentials is not None:
            cred_list = self.to_csv(credentials)
            url = self.baseurl + f"object-store-remote-credentials?names={cred_list}"
            msg = f"object store remote credentials: {cred_list}"
        else:
            url = self.baseurl + f"object-store-remote-credentials"
            msg = f"object store remote credentials"
            
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Get subnets
    def get_subnets(self, subnets=None, dumpjson=False):
        if subnets is not None:
            sub_list = self.to_csv(subnets)
            url = self.baseurl + f"subnets?names={sub_list}"
            msg = f"subnets: {sub_list}"
        else:
            url = self.baseurl + "subnets"
            msg = "subnets"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get network interfaces
    def get_interfaces(self, interfaces=None, dumpjson=False):
        if interfaces is not None:
            iface_list = self.to_csv(interfaces)
            url = self.baseurl + f"network-interfaces?names={iface_list}"
            msg = f"network interfaces: {iface_list}"
        else:
            url = self.baseurl + "network-interfaces"
            msg = "network interfaces"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Get filesystem replica links
    def get_filesytem_replica_links(self, filesystems=None, dumpjson=False):
        if filesystems is not None:
            fs_list = self.to_csv(filesystems)
            url = self.baseurl + f"file-system-replica-links?local_file_system_names={fs_list}" 
            msg = f"filesystem replica links: {fs_list}"
        else:
            url = self.baseurl + "file-system-replica-links" 
            msg = "filesystem replica links"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get filesystem snapshots
    def get_filesystem_snapshots(self, snapshots=None, dumpjson=False):
        if snapshots is not None:
            snap_list = self.to_csv(snapshots)
            url = self.baseurl + f"file-system-snapshots?names_or_owner_names={snap_list}"
            msg = f"filesystem snapshots: {snap_list}"
        else:
            url = self.baseurl + f"file-system-snapshots"
            msg = f"filesystem snapshots"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get snapshot polices
    def get_snapshot_policies(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"policies?names={pol_list}"
            msg = f"filesystem snapshot policys: {pol_list}"
        else:
            url = self.baseurl + "policies"
            msg = "filesystem snapshot policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get snapshot policies attached 
    def get_filesystems_attached_to_snapshot_policy(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"file-systems/policies?policy_names={pol_list}"
            msg = f"attached snapshot policy: {pol_list}"
        else:
            url = self.baseurl + f"file-systems/policies"
            msg = f"attached snapshot policies"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
       
    # Get connected NFS clients
    def get_nfs_clients(self, dumpjson=False):
        url = self.baseurl + "arrays/clients/performance"
        msg = "NFS clients"
        data = self.REST_Request("get", url, msg)
        return data
        
    # Get remote array connections
    def get_array_connections(self, dumpjson=False):
        url = self.baseurl + "array-connections"
        msg = "array connections"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
        
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
        
    # Post a bucket replica link (ENDPOINT BROKEN)
    def post_bucket_replica_link(self, bucket, remote_credential, payload):
        url = self.baseurl + f"bucket-replica-links?local_bucket_names={bucket}&remote_bucket_names={bucket}&remote_credentials_names={remote_credential}"
        msg = f"bucket replica link: {bucket} with remote credential: {remote_credential}"
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
        
    # Post an object store remote credential (formatted <remote-name>/<credentials-name>)
    def post_object_store_remote_credential(self, credential_name, payload):
        url = self.baseurl + f"object-store-remote-credentials?names={credential_name}"
        msg = f"object store remote credential: {credential_name}"
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

    # Post a filesystem replica link (Replica Link ID required)
    def post_filesystem_replica_link(self, filesystem_id, payload):
        url = self.baseurl + f"file-system-replica-links?ids={filesystem_id}"
        msg = f"filesystem replica link: {filesystem_id}"
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
        
    # Patch a bucket
    def patch_bucket(self, bucket, payload):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"filesystem bucket: {bucket}"
        data = self.REST_Request("patch", url, msg, payload=payload)

        if data is not None:
            return data["items"][0]
        

    ##########################
    ### DELETE API Section ###
    ##########################
    

    # Delete a filesytem
    def delete_filesystem(self, filesystem):
        url = self.baseurl + f"file-systems?names={filesystem}"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("delete", url, msg)

    # Delete an object store user
    def delete_object_store_user(self, object_user):
        url = self.baseurl + f"object-store-users?names={object_user}"
        msg = f"object store user: {object_user}"
        data = self.REST_Request("delete", url, msg)

    # Delete an object store access key
    def delete_object_store_access_key(self, access_key):
        url = self.baseurl + f"object-store-access-keys?names={access_key}"
        msg = f"access key: {access_key}"
        data = self.REST_Request("delete", url, msg)

    # Delete an object store remote credential
    def delete_object_store_remote_credential(self, credential_name):
        url = self.baseurl + f"object-store-remote_credentials?names={credential_name}"
        msg = f"credential name: {credential_name}"
        data = self.REST_Request("delete", url, msg)
    
    # Delete a bucket replica link
    def delete_bucket_replica_link(self, local_bucket):
        url = self.baseurl + f"bucket-replica-links?local_bucket_names={local_bucket}"
        msg = f"bucket replica link: {local_bucket}"
        data = self.REST_Request("delete", url, msg)

    # Delete a filesystem replica link
    def delete_filesystem_replica_link(self, local_filesystem):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={local_filesystem}&cancel_in_progress_transfers=true"
        msg = f"filesystem replica link: {local_filesystem}"
        data = self.REST_Request("delete", url, msg)

    # Delete a filesystem snapshot
    def delete_filesystem_snapshot(self, snapshot):
        url = self.baseurl + f"file-system-snapshots?names={snapshot}"
        msg = f"snapshot: {snapshot}"
        data = self.REST_Request("delete", url, msg)
        
