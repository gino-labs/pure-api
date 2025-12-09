#!/usr/bin/env python3
import os
import sys
import json
import socket
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
        self.PB1_NAME = os.getenv("PB1_NAME")
        self.PB2_NAME = os.getenv("PB2_NAME")
        self.PB1_REPLICATION = os.getenv("PB1_REPLICATION")
        self.PB2_REPLICATION = os.getenv("PB2_REPLICATION")
        self.PB1_API_TOKEN = os.getenv("PB1_API_TOKEN")
        self.PB2_API_TOKEN = os.getenv("PB2_API_TOKEN")
        self.PB_DATA_VLAN = os.getenv("PB_DATA_VLAN")

    # Return Environment variables as dictionary
    def get_site_vars(self):
        site_vars = {
            "pb1": self.PB1,
            "pb2": self.PB2,
            "pb1_mgt": self.PB1_MGT,
            "pb2_mgt": self.PB2_MGT,
            "pb1_replication": self.PB1_REPLICATION,
            "pb2_replication": self.PB2_REPLICATION,
            "legacy_api_token": self.PB1_API_TOKEN,
            "s200_api_token": self.PB2_API_TOKEN,
            "data_vlan": self.PB_DATA_VLAN
        }
        return site_vars
    
    # Return only pb1 variables
    def get_pb1_vars(self, var_dict=False):
        if var_dict:
            pb1_vars = {
                "pb1": self.PB1,
                "pb1_mgt": self.PB1_MGT,
                "api_token": self.PB1_API_TOKEN
            }
        else:
            pb1_vars = [self.PB1, self.PB1_MGT, self.PB1_API_TOKEN]
        return pb1_vars

    # Return only pb2 variables
    def get_pb2_vars(self, var_dict=False):
        if var_dict:
            pb2_vars = {
                "pb2": self.PB2,
                "pb2_mgt": self.PB2_MGT,
                "api_token": self.PB2_API_TOKEN
            }
        else:
            pb2_vars = [self.PB2, self.PB2_MGT, self.PB2_API_TOKEN]
        return pb2_vars
    
     # Get pb1 mgt ip
    def get_pb1_mgt_host(self, ip_addr=True):
        if ip_addr and self.PB1_MGT:
            return socket.gethostbyname(self.PB1_MGT)
        return self.PB1_MGT

    # Get pb2 mgt ip
    def get_pb2_mgt_host(self, ip_addr=True):
        if ip_addr and self.PB2_MGT:
            return socket.gethostbyname(self.PB2_MGT)
        return self.PB2_MGT

    # Get pb1 data ip
    def get_pb1_data_host(self, ip_addr=False):
        if ip_addr and self.PB1:
            return socket.gethostbyname(self.PB1)
        return self.PB1

    # Get pb2 data ip
    def get_pb2_data_host(self, ip_addr=False):
        if ip_addr and self.PB2:
            return socket.gethostbyname(self.PB2)
        return self.PB2
    
    # Get pb1 replication ip
    def get_pb1_replication_ip(self):
        return self.PB1_REPLICATION
    
    # Get pb2 replication ip
    def get_pb2_replication_ip(self):
        return self.PB2_REPLICATION
    
    # Set pb1 data ip
    def set_pb1_data_host(self, host_or_ip):
        self.PB1 = host_or_ip

    # Set pb2 data ip
    def set_pb2_data_host(self, host_or_ip):
        self.PB2 = host_or_ip
    
    # Set pb1 replication ip
    def set_pb1_replication_ip(self, host_or_ip):
        self.PB1_REPLICATION = host_or_ip
    
    # Set pb2 replication ip
    def set_pb2_replication_ip(self, host_or_ip):
        self.PB2_REPLICATION = host_or_ip
    
    # Get local ip of host executing scripts
    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # address doesn't need to be reachable
            s.connect(("108.156.201.129", 80))
            return s.getsockname()[0]
        finally:
            s.close()

    # Get PB1 hostnames / cnames
    def get_pb1_name(self):
        return self.PB1_NAME
    
    # Get PB1 hostnames / cnames
    def get_pb2_name(self):
        return self.PB2_NAME
    
    # Get data vlan
    def get_data_vlan(self):
        return int(self.PB_DATA_VLAN)
    
    # Get site initials
    def get_site_initials(self):
        return self.get_pb2_name()[:2]

# Custom exception class built for handling api errors 
class ApiError(Exception):
    def __init__(self, message, code, context):
        self.code = code
        self.context = context
        self.message = message
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

    def check_details(self, show_context=False, show_code=True, show_message=True, ask_to_continue=True):
        self.logger.write_log(f"API error code: {self.code}", show_output=show_code, end_print="\n")
        self.logger.write_log(f"API error context: \"{self.context}\"", show_output=show_context, end_print="\n")
        self.logger.write_log(f"API error message: \"{self.message}\"", show_output=show_message)
        if ask_to_continue:
            self.ask_to_continue_loop()

class FlashBladeAPI:
    def __init__(self, data_ip, mgt_ip, api_token):
        try:
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
    def Parse_Data(self, data, dump=False, no_dict=True):
        if "errors" not in data:
            try:
                if "items" not in data:
                    if dump:
                        self.logger.write_log("Items not found. See below.", jsondata=data, show_output=dump)
                    return data
                elif len(data["items"]) == 1:
                    if dump:
                        self.logger.write_log("Debug: See parsed data.", jsondata=data["items"][0], show_output=dump)
                    if no_dict:
                        return data["items"]
                    else:
                        return data["items"][0]
                elif len(data["items"]) == 0:
                    self.logger.write_log("Zero items returned from parsed data list.", show_output=False)
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
    def get_endpoint(self, endpoint, params=None, dumpjson=False, no_dict=True, raw=False):
        if params is not None:
            url = self.baseurl + endpoint + f"?{params}"
            msg = endpoint
        else:
            url = self.baseurl + endpoint
            msg = endpoint

        data = self.REST_Request("get", url, msg)
        if raw:
            if dumpjson:
                print(json.dumps(data, indent=4), end="\n\n")
            return data
        else:
            return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)

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
    def get_filesystems(self, filesystems=None, dumpjson=False, no_dict=True):
        if filesystems is not None:
            fs_list = self.to_csv(filesystems)
            url = self.baseurl + f"file-systems?names={fs_list}"
            msg = f"filesystems: {filesystems}"      
        else:
            url = self.baseurl + "file-systems"
            msg = "filesystems"
            
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get object store accounts
    def get_object_store_accounts(self, accounts=None, dumpjson=False, no_dict=True):
        if accounts is not None:
            acct_list = self.to_csv(accounts)
            url = self.baseurl + f"object-store-accounts?names={acct_list}"
            msg = f"object store accounts: {acct_list}"
        else:
            url = self.baseurl + "object-store-accounts"
            msg = "object store accounts"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get buckets
    def get_buckets(self, buckets=None, dumpjson=False, no_dict=True):
        if buckets is not None:
            buck_list = self.to_csv(buckets)
            url = self.baseurl + f"buckets?names={buck_list}"
            msg = f"buckets: {buck_list}"
        else:
            url = self.baseurl + "buckets"
            msg = "buckets"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get bucket replica links
    def get_bucket_replia_links(self, buckets=None, dumpjson=False, no_dict=True):
        if buckets is not None:
            buck_list = self.to_csv(buckets)
            url = self.baseurl + f"bucket-replica-links?local_bucket_names={buck_list}"
            msg = f"bucket replica links: {buck_list}"
        else:
            url = self.baseurl + f"bucket-replica-links"
            msg = f"bucket replica links"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get object store users
    def get_object_store_users(self, users=None, dumpjson=False, no_dict=True):
        if users is not None:
            user_list = self.to_csv(users)
            url = self.baseurl + f"object-store-users?names={user_list}"
            msg = f"object store users: {users}"
        else:
            url = self.baseurl + f"object-store-users"
            msg = f"object store users"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)

    # Get object store access keys
    def get_object_store_access_keys(self, keys=None, dumpjson=False, no_dict=True):
        if keys is not None:
            key_list = self.to_csv(keys)
            url = self.baseurl + f"object-store-access-keys?names={key_list}"
            msg = f"object store access keys: {key_list}"
        else:
            url = self.baseurl + f"object-store-access-keys"
            msg = "object store access keys"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get object store remote credentials
    def get_object_store_remote_credentials(self, credentials=None, dumpjson=False, no_dict=True):
        if credentials is not None:
            cred_list = self.to_csv(credentials)
            url = self.baseurl + f"object-store-remote-credentials?names={cred_list}"
            msg = f"object store remote credentials: {cred_list}"
        else:
            url = self.baseurl + f"object-store-remote-credentials"
            msg = f"object store remote credentials"
            
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)

    # Get subnets
    def get_subnets(self, subnets=None, dumpjson=False, no_dict=True):
        if subnets is not None:
            sub_list = self.to_csv(subnets)
            url = self.baseurl + f"subnets?names={sub_list}"
            msg = f"subnets: {sub_list}"
        else:
            url = self.baseurl + "subnets"
            msg = "subnets"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get network interfaces
    def get_interfaces(self, interfaces=None, dumpjson=False, no_dict=True):
        if interfaces is not None:
            iface_list = self.to_csv(interfaces)
            url = self.baseurl + f"network-interfaces?names={iface_list}"
            msg = f"network interfaces: {iface_list}"
        else:
            url = self.baseurl + "network-interfaces"
            msg = "network interfaces"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)

    # Get filesystem replica links
    def get_filesystem_replica_links(self, filesystems=None, dumpjson=False, no_dict=True):
        if filesystems is not None:
            fs_list = self.to_csv(filesystems)
            url = self.baseurl + f"file-system-replica-links?local_file_system_names={fs_list}" 
            msg = f"filesystem replica links: {fs_list}"
        else:
            url = self.baseurl + "file-system-replica-links" 
            msg = "filesystem replica links"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get filesystem snapshots
    def get_filesystem_snapshots(self, snapshots=None, dumpjson=False, no_dict=True):
        if snapshots is not None:
            snap_list = self.to_csv(snapshots)
            url = self.baseurl + f"file-system-snapshots?names_or_owner_names={snap_list}"
            msg = f"filesystem snapshots: {snap_list}"
        else:
            url = self.baseurl + f"file-system-snapshots"
            msg = f"filesystem snapshots"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get snapshot polices
    def get_snapshot_policies(self, policies=None, dumpjson=False, no_dict=True):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"policies?names={pol_list}"
            msg = f"filesystem snapshot policies: {pol_list}"
        else:
            url = self.baseurl + "policies"
            msg = "filesystem snapshot policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
        
    # Get snapshot policies attached 
    def get_snapshot_policy_members(self, policies=None, dumpjson=False, no_dict=True):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"file-systems/policies?policy_names={pol_list}"
            msg = f"attached snapshot policy: {pol_list}"
        else:
            url = self.baseurl + f"file-systems/policies"
            msg = f"attached snapshot policies"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
       
    # Get connected NFS clients
    def get_nfs_clients(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "arrays/clients/performance"
        msg = "NFS clients"
        data = self.REST_Request("get", url, msg)
        return data
        
    # Get remote array connections
    def get_array_connections(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "array-connections"
        msg = "array connections"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get directory services
    def get_directory_services(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "directory-services"
        msg = "directory services"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get directory service roles
    def get_directory_service_roles(self, role_names=None, dumpjson=False, no_dict=True):
        if role_names is not None:
            role_list = self.to_csv(role_names)
            url = self.baseurl + f"directory-services/roles?role_names={role_list}"
            msg = f"directory service roles: {role_names}"
        else:
            url = self.baseurl + "directory-services/roles"
            msg = "directory service roles"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get DNS configuration
    def get_dns(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "dns"
        msg = "DNS"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get array configurations
    def get_array_configurations(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "arrays"
        msg = "array configurations"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get array connections
    def get_array_connections(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "array-connections"
        msg = "array connections"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get certifcates
    def get_certificates(self, certificates=None, dumpjson=False, no_dict=True):
        if certificates is not None:
            cert_list = self.to_csv(certificates)
            url = self.baseurl + f"certificates?names={cert_list}"
            msg = f"certificates: {certificates}"
        else:
            url = self.baseurl + "certificates"
            msg = "certifcates"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get certificate groups
    def get_certificate_groups(self, groups=None, dumpjson=False, no_dict=True):
        if groups is not None:
            group_list = self.to_csv(groups)
            url = self.baseurl + f"certificate-groups?names={group_list}"
            msg = f"certificate groups: {groups}"
        else:
            url = self.baseurl + "certificate-groups"
            msg = "certificate groups"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get certificate group memebers
    def get_certificate_group_members(self, group, dumpjson=False, no_dict=True):
        url = self.baseurl + f"certificate-groups/certificates?certificate_group_names={group}"
        msg = "certificate group members"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get NFS export policies
    def get_nfs_export_policies(self, policies=None, dumpjson=False, no_dict=True):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"nfs-export-policies?names={pol_list}"
            msg = f"nfs export policies: {pol_list}"
        else:
            url = self.baseurl + "nfs-export-policies"
            msg = "nfs export policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get SMB client policies
    def get_smb_client_policies(self, policies=None, dumpjson=False, no_dict=True):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"smb-client-policies?names={pol_list}"
            msg = f"smb client policies: {pol_list}"
        else:
            url = self.baseurl + "smb-client-policies"
            msg = "smb client policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get SMB share policies
    def get_smb_share_policies(self, policies=None, dumpjson=False, no_dict=True):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"smb-share-policies?names={pol_list}"
            msg = f"smb share policies: {pol_list}"
        else:
            url = self.baseurl + "smb-share-policies"
            msg = "smb share policies"
        
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get syslog servers
    def get_syslog_servers(self, syslog_names=None, dumpjson=False, no_dict=True):
        if syslog_names is not None:
            syslog_list = self.to_csv(syslog_names)
            url = self.baseurl + f"syslog-servers?names={syslog_list}"
            msg = f"syslog servers: {syslog_list}"
        else:
            url = self.baseurl + f"syslog-servers"
            msg = f"syslog servers"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get connection key
    def get_connection_key(self, dumpjson=False, no_dict=True):
        url = self.baseurl + "array-connections/connection-key"
        msg = "connection key"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get users quotas per file system
    def get_user_quotas(self, filesystem, dumpjson=False, no_dict=True):
        url = self.baseurl + f"quotas/users?file_system_names={filesystem}"
        msg = f"{filesystem} user quotas"
        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)
    
    # Get users file system usage
    def get_users_filesystem_usage(self, filesystem, uids=None, dumpjson=False, no_dict=True):
        if uids is not None:
            uid_list = self.to_csv(uids)
            url = self.baseurl + f"usage/users?file_system_names={filesystem}&uids={uid_list}"
            msg = f"{filesystem} usage for UIDs: {uid_list}"
        else:
            url = self.baseurl + f"usage/users?file_system_names={filesystem}"
            msg = f"{filesystem} usage by UIDs"

        data = self.REST_Request("get", url, msg)
        return self.Parse_Data(data, dump=dumpjson, no_dict=no_dict)

 
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
    
    # Post certificate
    def post_certificate(self, certificate_name, payload, dumpjson=False):
        url = self.baseurl + f"certificates?names={certificate_name}"
        msg = f"certifcate: {certificate_name}"
        data = self.REST_Request("post", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Post certificate to a certificate group
    def post_certificate_to_group(self, certificate, group, dumpjson=False):
        url = self.baseurl + f"certificate-groups/certificates?certificate_names={certificate}&certificate_group_names={group}"
        msg = f"group/certificate: {group}/{certificate}"
        data = self.REST_Request("post", url, msg)
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
    
    # Patch directory services
    def patch_directory_services(self, name, payload, dumpjson=False):
        url = self.baseurl + f"directory-services?names={name}"
        msg = f"directory service: {name}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Patch directory service role
    def patch_directory_service_role(self, role_name, payload, dumpjson=False):
        url = self.baseurl + f"directory-services/roles?role_names={role_name}"
        msg = f"directory service role: {role_name}"
        data = self.REST_Request("patch", url, msg, payload=payload)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Patch DNS
    def patch_dns(self, dns, payload, dumpjson=False):
        url = self.baseurl + f"dns?names={dns}"
        msg = f"DNS: {dns}"
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

    # Delete a bucket
    def delete_bucket(self, bucket, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
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
        url = self.baseurl + f"object-store-remote-credentials?names={credential_name}"
        msg = f"credential name: {credential_name}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete an object store account
    def delete_object_store_account(self, account, dumpjson=False):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
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
    
    # Delete snapshot policies
    def delete_snapshot_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"policies?names={policy}"
        msg = f"snapshot policy: {policy}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a NFS export policy
    def delete_nfs_export_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"NFS export policy: {policy}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a SMB client policy
    def delete_smb_client_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"smb-client-policies?names={policy}"
        msg = f"SMB client policy: {policy}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a SMB client policy
    def delete_smb_share_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"smb-share-policies?names={policy}"
        msg = f"SMB share policy: {policy}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a network interface
    def delete_interface(self, interface, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete a subnet
    def delete_subnet(self, subnet, dumpjson=False):
        url = self.baseurl + f"subnets?names={subnet}"
        msg = f"subnet: {subnet}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
        
    # Delete an array connection
    def delete_array_connection(self, remote_name, dumpjson=False):
        url = self.baseurl + f"array-connections?remote_names={remote_name}"
        msg = f"array connection: {remote_name}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete syslog server
    def delete_syslog_server(self, syslog_server, dumpjson=False):
        url = self.baseurl + f"syslog-servers?names={syslog_server}"
        msg = f"syslog server: {syslog_server}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)
    
    # Delete certificate
    def delete_certifcate(self, certificate, dumpjson=False):
        url = self.baseurl + f"certificates?names={certificate}"
        msg = f"certificate: {certificate}"
        data = self.REST_Request("delete", url, msg)
        return self.Parse_Data(data, dump=dumpjson)