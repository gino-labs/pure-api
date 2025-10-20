#!/usr/bin/env python3
import os
import sys
import json
import urllib3
import requests
from purefb_log import PureLog

# Disabling Insecure Requests Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a class for site enviornment variables
class SiteVars:
    def __init__(self):
        # Environment variables sourced from shell 
        self.PB1 = os.getenv("PB1")
        self.PB2 = os.getenv("PB2")
        self.PB1_MGT = os.getenv("PB1_MGT")
        self.PB2_MGT = os.getenv("PB2_MGT")
        self.LOCAL_IP = os.getenv("LOCAL_IP")
        self.API_TOKEN = os.getenv("API_TOKEN")
        self.API_TOKEN_S200 = os.getenv("API_TOKEN_S200")
        self.MIGRATION_POLICY = os.getenv("MIGRATION_POLICY")
        self.REPLICATION_CUTOFF = os.getenv("REPLICATION_CUTOFF")

    # Return Environment variables as dictionary
    def get_site_vars(self):
        site_vars = {
            "pb1": self.PB1,
            "pb2": self.PB2,
            "pb1_mgt": self.PB1_MGT,
            "pb2_mgt": self.PB2_MGT,
            "local_ip": self.LOCAL_IP,
            "legacy_api_token": self.API_TOKEN,
            "s200_api_token": self.API_TOKEN_S200,
            "migration_policy": self.MIGRATION_POLICY,
            "replication_cutoff": self.REPLICATION_CUTOFF
        }
        return site_vars
    
    # Return only pb1 variables
    def get_pb1_vars(self, var_dict=False):
        if var_dict:
            pb1_vars = {
                "pb1": self.PB1,
                "pb1_mgt": self.PB1_MGT,
                "api_token": self.API_TOKEN
            }
        else:
            pb1_vars = [self.PB1, self.PB1_MGT, self.API_TOKEN]
        return pb1_vars

    # Return only pb2 variables
    def get_pb2_vars(self, var_dict=False):
        if var_dict:
            pb2_vars = {
                "pb2": self.PB2,
                "pb2_mgt": self.PB2_MGT,
                "api_token": self.API_TOKEN_S200
            }
        else:
            pb2_vars = [self.PB2, self.PB2_MGT, self.API_TOKEN_S200]
        return pb2_vars
    
    # Get pb1 data ip
    def get_pb1_data_ip(self):
        return self.PB1

    # Get pb2 data ip
    def get_pb2_data_ip(self):
        return self.PB2
    
    # Get local ip of host executing scripts
    def get_local_ip(self):
        return self.LOCAL_IP


# Custom exception class built for handling api errors 
class ApiError(Exception):
    def __init__(self, message, code, context, ask_to_continue=True):
        self.code = code
        self.context = context
        self.message = message
        self.ask_to_continue = ask_to_continue
        self.logger = PureLog()
        super().__init__(f"[Code: {code}] {message}")

    def ask_to_continue_loop(self):
        user_input = input("Would you like to continue? (y/n): ")[:1].lower()
        while user_input not in ("y", "n"):
            user_input = input("Please enter y/n to stop or continue the script: ")[:1].lower()
        print()
        if user_input == "n":
            print("Exiting script...")
            sys.exit(1)
        else:
            self.logger.write_log(f"Continuing with script after encountering error related to: \"{self.context}\"", show_output=True)
            return True

    def check_details(self, skip_ask_to_continue=False, show_code=False, show_context=False, show_message=True):
        self.logger.write_log(f"API error code: {self.code}", show_output=show_code, end_print="\n")
        self.logger.write_log(f"API error context: \"{self.context}\"", show_output=show_context, end_print="\n")
        self.logger.write_log(f"API error message: \"{self.message}\"", show_output=show_message)
        if self.ask_to_continue and not skip_ask_to_continue:
            self.ask_to_continue_loop()

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
            self.logger = PureLog()
        except requests.RequestException as e:
            e_msg = f"\nError RequestException occured. Please check your environment variables are correctly set."
            print(f"{e_msg}")
            print()
            sys.exit(1)

    # Get site environment variables as a dictionary
    def get_env_vars(self):
        env_vars = {
            "name": self.name,
            "data_ip": self.data_ip,
            "mgt_ip": self.mgt_ip,
            "api_token": self.api_token,
            "baseurl": self.baseurl
        }
        return env_vars
    
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
    
    # Function to prompt user whether or not to continue
    def continue_check(self, post_msg=None):
        user_input = input("Would you like to continue? (y/n): ")[:1].lower()
        while user_input not in ("y", "n"):
            user_input = input("Please enter y/n to stop or continue the script: ")[:1].lower()
        print()
        if user_input == "n":
            print("Exiting script...")
            sys.exit(1)
        else:
            if post_msg:
                self.logger.write_log(post_msg, show_output=True)
            return True

    # Make a api request
    def REST_Request(self, method, url, message, payload=None, show_output=True):
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
            self.logger.write_log(msg, show_output=show_output)
            if method == "delete":
                return {"status_code": response.status_code, "text": response.text}
            else:
                return response.json()
        else:
            try:
                msg = f"{method.upper()} failure for {message}"
                self.logger.write_log(msg, show_output=True, end_print="\n")
                self.logger.write_log(f"HTTP response status code: {response.status_code}", show_output=True)
                errors = response.json()
                return errors
            except Exception as e:
                print(f"Exception occurred: {type(e).__name__} -> {e}")
                sys.exit(1)

    # Parse json data or rest request items
    def Parse_Data(self, data, dump=False):
        if "errors" not in data:
            try:
                if "items" not in data:
                    if dump:
                        self.logger.write_log("Items not found. See below.", jsondata=data, show_output=dump)
                    return data
                elif len(data["items"]) == 1:
                    if dump:
                        self.logger.write_log("Debug: See parsed data.", jsondata=data["items"][0], show_output=dump)
                    return data["items"][0]
                elif len(data["items"]) == 0:
                    self.logger.write_log("Zero items returned from parsed data list.", show_output=True)
                    return data["items"]
                else:
                    if dump:
                        self.logger.write_log("Debug: See parsed data.", jsondata=data["items"], show_output=dump)
                    return data["items"]
            except Exception as e:
                self.logger.write_log(f"Exception has occured: {type(e).__name__} -> {e}", show_output=True)
                self.logger.write_log("Returning full unparsed json data.", show_output=True)
                if dump:
                    self.logger.write_log("Json output for data", jsondata=data, show_output=dump)
                return data
        else:
            errors = {
                "error_code": data["errors"][0]["code"],
                "error_context": data["errors"][0]["context"],
                "error_message": data["errors"][0]["message"]
            }
            raise ApiError(errors["error_message"], errors["error_code"], errors["error_context"])

    # Helper function to return a csv string or single string
    def to_csv(self, value):
        if isinstance(value, str):
            return value
        return ",".join(value)
        

    #######################
    ### GET API Section ###
    #######################

    # General get request by passing endpoint
    def get_endpoint(self, endpoint, params=None, dumpjson=False):
        if params is not None:
            url = self.baseurl + endpoint + f"?{params}"
            msg = endpoint
        else:
            url = self.baseurl + endpoint
            msg = endpoint

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Get api version used by blade
    def get_api_version(self, dumpjson=False):
        url = f"https://{self.mgt_ip}/api/api_version"
        msg = "API version"
        data = self.REST_Request("get", url, msg)

        if "errors" not in data:
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
            msg = f"filesystem snapshot policies: {pol_list}"
        else:
            url = self.baseurl + "policies"
            msg = "filesystem snapshot policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Get snapshot policies attached 
    def get_snapshot_policy_members(self, policies=None, dumpjson=False):
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
    
    # Get directory services
    def get_directory_services(self, dumpjson=False):
        url = self.baseurl + "directory-services"
        msg = "directory services"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get DNS configuration
    def get_dns(self, dumpjson=False):
        url = self.baseurl + "dns"
        msg = "DNS"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get array configurations
    def get_array_configurations(self, dumpjson=False):
        url = self.baseurl + "arrays"
        msg = "array configurations"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get array connections
    def get_array_connections(self, dumpjson=False):
        url = self.baseurl + "array-connections"
        msg = "array connections"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get certifcates
    def get_certificates(self, dumpjson=False):
        url = self.baseurl + "certificates"
        msg = "certifcates"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get NFS export policies
    def get_nfs_export_policies(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"nfs-export-policies?names={pol_list}"
            msg = f"nfs export policies: {pol_list}"
        else:
            url = self.baseurl + "nfs-export-policies"
            msg = "nfs export policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get syslog servers
    def get_syslog_servers(self, syslog_names=None, dumpjson=False):
        if syslog_names is not None:
            syslog_list = self.to_csv(syslog_names)
            url = self.baseurl + f"syslog-servers?names={syslog_list}"
            msg = f"syslog servers: {syslog_list}"
        else:
            url = self.baseurl + f"syslog-servers"
            msg = f"syslog servers"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Get connection key
    def get_connection_key(self, dumpjson=False):
        url = self.baseurl + "array-connections/connection-key"
        msg = "connection key"
        data = self.REST_Request("get", url, msg)

        return self.Parse_Data(data, dump=dumpjson)

 
    ########################
    ### POST API Section ###
    ########################


    # Post a filesystem (default NFS)
    def post_filesystem(self, filesystem, payload, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}&default_exports=nfs"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post an object store account
    def post_object_store_account(self, account, payload, dumpjson=False):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)

    # Post a bucket
    def post_bucket(self, bucket, payload, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post a bucket replica link (ENDPOINT BROKEN)
    def post_bucket_replica_link(self, bucket, remote_credential, payload, dumpjson=False):
        url = self.baseurl + f"bucket-replica-links?local_bucket_names={bucket}&remote_bucket_names={bucket}&remote_credentials_names={remote_credential}"
        msg = f"bucket replica link: {bucket} with remote credential: {remote_credential}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post an object store user
    def post_object_store_user(self, user, dumpjson=False):
        url = self.baseurl + f"object-store-users?names={user}&full_access=true"
        msg = f"object store user: {user}"
        data = self.REST_Request("post", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post an object store access key (Secret key shown once in response)
    def post_object_store_access_key(self, user, payload, dumpjson=False):
        url = self.baseurl + "object-store-access-keys"
        msg = f"object store access key: {user}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post an object store remote credential (formatted <remote-name>/<credentials-name>)
    def post_object_store_remote_credential(self, credential_name, payload, dumpjson=False):
        url = self.baseurl + f"object-store-remote-credentials?names={credential_name}"
        msg = f"object store remote credential: {credential_name}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post a subnet
    def post_subnet(self, subnet, payload, dumpjson=False):
        url = self.baseurl + f"subnets?names={subnet}"
        msg = f"subnet: {subnet}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)

    # Post a network interface
    def post_interface(self, interface, payload, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)

    # Post a filesystem replica link (Replica Link ID required)
    def post_filesystem_replica_link(self, filesystem, remote_array, payload, dumpjson=False):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={filesystem}&remote_file_system_names={filesystem}&remote_names={remote_array}"
        msg = f"filesystem replica link: {filesystem}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post a filesystem snapshot
    def post_filesystem_snapshot(self, filesystem, snapshot, replicate=True, dumpjson=False):
        if replicate:
            url = self.baseurl + f"file-system-snapshots?source_names={filesystem}&send=true"
        else:
            url = self.baseurl + f"file-system-snapshots?source_names={filesystem}"
        msg = f"filesytem snapshot: {snapshot} for {filesystem}"
        data = self.REST_Request("post", url, msg, payload={"suffix":snapshot})
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post snapshot scheduling policy to a filesystem
    def post_snapshot_policy_to_filesystem(self, policy, filesystem, dumpjson=False):
        url = self.baseurl + f"file-systems/policies?member_names={filesystem}&policy_names={policy}"
        msg = f"snapshot policy {policy} to {filesystem}"
        data = self.REST_Request("post", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Post snapshot policy
    def post_snapshot_policy(self, policy, payload, dumpjson=False):
        url = self.baseurl + f"policies?names={policy}"
        msg = f"filesystem snapshot policies: {policy}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Post NFS export policy
    def post_nfs_export_policy(self, policy, payload, dumpjson=False):
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"NFS export policiy: {policy}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Post syslog server
    def post_syslog_server(self, syslog_name, uri, dumpjson=False):
        url = self.baseurl + f"syslog-servers?names={syslog_name}"
        msg = f"syslog server: {syslog_name}"
        data = self.REST_Request("post", url, msg, payload={"uri": uri})
        return self.Parse_Data(data, dump=dumpjson)
    
    # Post connection key
    def post_connection_key(self, dumpjson=False):
        url = self.baseurl + "array-connections/connection-key"
        msg = "connection key"
        data = self.REST_Request("post", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Post array connection 
    def post_array_connection(self, payload, dumpjson=False):
        url = self.baseurl + "array-connections"
        msg = "array connection"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)


    #########################
    ### PATCH API Section ###
    #########################
        
        
    # Patch a filesystem
    def patch_filesystem(self, filesystem, payload, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}"
        if payload.get("requested_promotion_state") == "demoted":
            url += "&discard_non_snapshotted_data=true"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
    
    def patch_nfs_export_policy(self, policy, payload, dumpjson=False):
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"NFS export policy: {policy}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Patch filesystem nfs rule if only if it doesn't already exist
    def patch_nfs_rule(self, filesystem, rule, remove=False, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}"
        msg = f"filesystem ({filesystem}) NFS rule: {rule}"
        target_fs = self.get_filesystems(filesystems=filesystem)
        if not remove and rule in target_fs["nfs"]["rules"]:
            self.logger.write_log(f"Rule {rule} for filesystem {filesystem} already exists.", show_output=True)
            return
        else:
            if remove:
                msg = "add " + msg
                edit_rule = "remove_rules"
            else:
                msg = "remove " + msg
                edit_rule = "add_rules"
            payload = {
                "nfs": {
                    edit_rule: rule
                }
            }
            data = self.REST_Request("patch", url, msg, payload=payload)
            return self.Parse_Data(data, dump=dumpjson)

    # Patch nfs rule to an export policy ### FIXME ###
    def patch_nfs_rule_to_policy(self, policy, perms="ro", client="*", access="no-squash", dumpjson=True):
        target_pol = self.get_nfs_export_policies(policies=policy)
        for rule in target_pol["rules"]:
            del rule["name"]
            del rule["id"]
            del rule["policy"]
            del rule["index"]
            del rule["policy_version"]
        rules = target_pol["rules"]
        
        rules.append(
            {
            "access": access,
            "client": client,
            "permission": perms
            }
        )
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"policy: {policy}"
        data = self.REST_Request("patch", url, msg, payload=rules)
        return self.Parse_Data(data, dump=dumpjson)


    # Patch a network interface
    def patch_interface(self, interface, payload, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)

    # Patch a snapshot
    def patch_filesystem_snapshot(self, snapshot, payload, dumpjson=False):
        url = self.baseurl + f"file-system-snapshots?names={snapshot}"
        if payload["destroyed"] == True:
            url = url + "&latest_replica=True"
        msg = f"filesystem snapshot: {snapshot}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Patch a bucket
    def patch_bucket(self, bucket, payload, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"filesystem bucket: {bucket}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
        

    ##########################
    ### DELETE API Section ###
    ##########################
    

    # Delete a filesytem
    def delete_filesystem(self, filesystem, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}"
        msg = f"filesystem: {filesystem}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Delete an object store user
    def delete_object_store_user(self, object_user, dumpjson=False):
        url = self.baseurl + f"object-store-users?names={object_user}"
        msg = f"object store user: {object_user}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Delete an object store access key
    def delete_object_store_access_key(self, access_key, dumpjson=False):
        url = self.baseurl + f"object-store-access-keys?names={access_key}"
        msg = f"access key: {access_key}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Delete an object store remote credential
    def delete_object_store_remote_credential(self, credential_name, dumpjson=False):
        url = self.baseurl + f"object-store-remote_credentials?names={credential_name}"
        msg = f"credential name: {credential_name}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a bucket replica link
    def delete_bucket_replica_link(self, bucket, remote_name, dumpjson=False):
        url = self.baseurl + f"bucket-replica-links?local_bucket_names={bucket}&remote_bucket_names={bucket}&remote_names={remote_name}"
        msg = f"bucket replica link: {bucket}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Delete a filesystem replica link
    def delete_filesystem_replica_link(self, filesystem, remote_array, dumpjson=False):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={filesystem}&remote_file_system_names={filesystem}&remote_names={remote_array}&cancel_in_progress_transfers=true"
        msg = f"filesystem replica link: {filesystem}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)

    # Delete a filesystem snapshot
    def delete_filesystem_snapshot(self, snapshot, dumpjson=False):
        url = self.baseurl + f"file-system-snapshots?names={snapshot}"
        msg = f"snapshot: {snapshot}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a NFS export policy
    def delete_nfs_export_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"nfs-export-policy?names={policy}"
        msg = f"NFS export policy: {policy}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a network interface
    def delete_interface(self, interface, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Delete an array connection
    def delete_array_connection(self, remote_name, dumpjson=False):
        url = self.baseurl + f"array-connections?remote_names={remote_name}"
        msg = f"array connection: {remote_name}"
        data = self.REST_Request("deleete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)