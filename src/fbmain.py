#!/usr/bin/env python3
import os
import sys
import json
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ApiError(Exception):
    def __init__(self, message: str, code: int, context: str):
        self.code = code
        self.context = context
        self.message = message
        super().__init__(f"API Error:\n\tCode: {code} \n\tContext: {context} \n\t{message}")

class FlashBladeAPI:
    def __init__(self, mgt_ip: str, api_token: str):
        self.mgt_ip = mgt_ip
        self.api_token = api_token
        self.baseurl = f"https://{mgt_ip}/api/2.latest/"
        self.session = requests.Session()
        self.api_versions = []
        self.name = ""
        self.id = ""
        self.os = ""
        self.version = ""
        self.product_type = ""
        self.time_zone = ""

    def configure(self):
        """Configure instance attributes after successful api login"""
        self.session.verify = False

        versions_url = f"https://{self.mgt_ip}/api/api_version"
        versions_response = self.session.request("GET", versions_url)
        versions_response.raise_for_status()
        version_data = versions_response.json()
        self.api_versions = version_data["versions"]

        self.session.headers["api-token"] = self.api_token

        login_url = f"https://{self.mgt_ip}/api/login"
        login_response = self.session.request("POST", login_url)
        login_response.raise_for_status()

        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": login_response.headers.get("x-auth-token")
        })

        array_response = self.session.get(self.baseurl + "arrays")
        array_response.raise_for_status()

        data = array_response.json()
        array = data["items"][0]

        self.name = array["name"]
        self.id = array["id"]
        self.os = array["os"]
        self.version = array["version"]
        self.product_type = array["product_type"]
        self.time_zone = array["time_zone"]

    def api_request(self, method: str, endpoint: str, **kwargs):
        """Generic base api request for all methods"""

        method = str(method).upper()
        if method not in ("GET", "POST", "PATCH", "DELETE"):
            raise ValueError(f"Invalid method: {method}")
        
        if method in ("POST", "PATCH"):
            response = self.session.request(method, self.baseurl + endpoint, json=kwargs["payload"])
        else:
            response = self.session.request(method, self.baseurl + endpoint)        
        
        response.raise_for_status()

        data = response.json() if response.content else None
        if data is None:
            return
            
        if "errors" in data:
            err_code = data["errors"][0]["code"]
            err_context = data["errors"][0]["context"]
            err_msg = data["errors"][0]["message"]
            raise ApiError(err_code, err_context, err_msg)
        
        return data

    # Helper function to return a csv string or single string
    def to_csv(self, value):
        if isinstance(value, str):
            return value
        return ",".join(value)
        

    #######################
    ### GET API Section ###
    #######################

    ## START REFACTORING HERE ## TODO ADD SOME TESTS ##

    # Get factory reset token
    def get_factory_reset_tokens(self, dumpjson=False):
        url = self.baseurl + "arrays/factory-reset-token"
        return self.parse_data(data, dumpjson=dumpjson)
            
    # Get Filesystems
    def get_filesystems(self, filesystems=None, dumpjson=False):
        if filesystems is not None:
            fs_list = self.to_csv(filesystems)
            url = self.baseurl + f"file-systems?names={fs_list}"
            msg = f"filesystems: {filesystems}"      
        else:
            url = self.baseurl + "file-systems"
            msg = "filesystems"
            
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get object store accounts
    def get_object_store_accounts(self, accounts=None, dumpjson=False):
        if accounts is not None:
            acct_list = self.to_csv(accounts)
            url = self.baseurl + f"object-store-accounts?names={acct_list}"
            msg = f"object store accounts: {acct_list}"
        else:
            url = self.baseurl + "object-store-accounts"
            msg = "object store accounts"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get buckets
    def get_buckets(self, buckets=None, dumpjson=False):
        if buckets is not None:
            buck_list = self.to_csv(buckets)
            url = self.baseurl + f"buckets?names={buck_list}"
            msg = f"buckets: {buck_list}"
        else:
            url = self.baseurl + "buckets"
            msg = "buckets"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get bucket replica links
    def get_bucket_replia_links(self, buckets=None, dumpjson=False):
        if buckets is not None:
            buck_list = self.to_csv(buckets)
            url = self.baseurl + f"bucket-replica-links?local_bucket_names={buck_list}"
            msg = f"bucket replica links: {buck_list}"
        else:
            url = self.baseurl + f"bucket-replica-links"
            msg = f"bucket replica links"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get object store users
    def get_object_store_users(self, users=None, dumpjson=False):
        if users is not None:
            user_list = self.to_csv(users)
            url = self.baseurl + f"object-store-users?names={user_list}"
            msg = f"object store users: {users}"
        else:
            url = self.baseurl + f"object-store-users"
            msg = f"object store users"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Get object store access keys
    def get_object_store_access_keys(self, keys=None, dumpjson=False):
        if keys is not None:
            key_list = self.to_csv(keys)
            url = self.baseurl + f"object-store-access-keys?names={key_list}"
            msg = f"object store access keys: {key_list}"
        else:
            url = self.baseurl + f"object-store-access-keys"
            msg = "object store access keys"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get object store remote credentials
    def get_object_store_remote_credentials(self, credentials=None, dumpjson=False):
        if credentials is not None:
            cred_list = self.to_csv(credentials)
            url = self.baseurl + f"object-store-remote-credentials?names={cred_list}"
            msg = f"object store remote credentials: {cred_list}"
        else:
            url = self.baseurl + f"object-store-remote-credentials"
            msg = f"object store remote credentials"
            
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Get subnets
    def get_subnets(self, subnets=None, dumpjson=False):
        if subnets is not None:
            sub_list = self.to_csv(subnets)
            url = self.baseurl + f"subnets?names={sub_list}"
            msg = f"subnets: {sub_list}"
        else:
            url = self.baseurl + "subnets"
            msg = "subnets"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get network interfaces
    def get_interfaces(self, interfaces=None, dumpjson=False):
        if interfaces is not None:
            iface_list = self.to_csv(interfaces)
            url = self.baseurl + f"network-interfaces?names={iface_list}"
            msg = f"network interfaces: {iface_list}"
        else:
            url = self.baseurl + "network-interfaces"
            msg = "network interfaces"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Get filesystem replica links
    def get_filesystem_replica_links(self, filesystems=None, dumpjson=False):
        if filesystems is not None:
            fs_list = self.to_csv(filesystems)
            url = self.baseurl + f"file-system-replica-links?local_file_system_names={fs_list}" 
            msg = f"filesystem replica links: {fs_list}"
        else:
            url = self.baseurl + "file-system-replica-links" 
            msg = "filesystem replica links"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get filesystem snapshots
    def get_filesystem_snapshots(self, snapshots=None, dumpjson=False):
        if snapshots is not None:
            snap_list = self.to_csv(snapshots)
            url = self.baseurl + f"file-system-snapshots?names_or_owner_names={snap_list}"
            msg = f"filesystem snapshots: {snap_list}"
        else:
            url = self.baseurl + f"file-system-snapshots"
            msg = f"filesystem snapshots"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get snapshot polices
    def get_snapshot_policies(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"policies?names={pol_list}"
            msg = f"filesystem snapshot policies: {pol_list}"
        else:
            url = self.baseurl + "policies"
            msg = "filesystem snapshot policies"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Get snapshot policies attached 
    def get_snapshot_policy_members(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"file-systems/policies?policy_names={pol_list}"
            msg = f"attached snapshot policy: {pol_list}"
        else:
            url = self.baseurl + f"file-systems/policies"
            msg = f"attached snapshot policies"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
       
    # Get connected NFS clients
    def get_nfs_clients(self, dumpjson=False):
        url = self.baseurl + "arrays/clients/performance"
        msg = "NFS clients"
        data = self.api_request("get", url, msg)
        return data
        
    # Get remote array connections
    def get_array_connections(self, dumpjson=False):
        url = self.baseurl + "array-connections"
        msg = "array connections"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get directory services
    def get_directory_services(self, dumpjson=False):
        url = self.baseurl + "directory-services"
        msg = "directory services"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get directory service roles
    def get_directory_service_roles(self, role_names=None, dumpjson=False):
        if role_names is not None:
            role_list = self.to_csv(role_names)
            url = self.baseurl + f"directory-services/roles?role_names={role_list}"
            msg = f"directory service roles: {role_names}"
        else:
            url = self.baseurl + "directory-services/roles"
            msg = "directory service roles"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get DNS configuration
    def get_dns(self, dumpjson=False):
        url = self.baseurl + "dns"
        msg = "DNS"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get array configurations
    def get_array_configurations(self, dumpjson=False):
        url = self.baseurl + "arrays"
        msg = "array configurations"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get array connections
    def get_array_connections(self, dumpjson=False):
        url = self.baseurl + "array-connections"
        msg = "array connections"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get certifcates
    def get_certificates(self, certificates=None, dumpjson=False):
        if certificates is not None:
            cert_list = self.to_csv(certificates)
            url = self.baseurl + f"certificates?names={cert_list}"
            msg = f"certificates: {certificates}"
        else:
            url = self.baseurl + "certificates"
            msg = "certifcates"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get certificate groups
    def get_certificate_groups(self, groups=None, dumpjson=False):
        if groups is not None:
            group_list = self.to_csv(groups)
            url = self.baseurl + f"certificate-groups?names={group_list}"
            msg = f"certificate groups: {groups}"
        else:
            url = self.baseurl + "certificate-groups"
            msg = "certificate groups"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get certificate group memebers
    def get_certificate_group_members(self, group, dumpjson=False):
        url = self.baseurl + f"certificate-groups/certificates?certificate_group_names={group}"
        msg = "certificate group members"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get NFS export policies
    def get_nfs_export_policies(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"nfs-export-policies?names={pol_list}"
            msg = f"nfs export policies: {pol_list}"
        else:
            url = self.baseurl + "nfs-export-policies"
            msg = "nfs export policies"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get SMB client policies
    def get_smb_client_policies(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"smb-client-policies?names={pol_list}"
            msg = f"smb client policies: {pol_list}"
        else:
            url = self.baseurl + "smb-client-policies"
            msg = "smb client policies"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get SMB share policies
    def get_smb_share_policies(self, policies=None, dumpjson=False):
        if policies is not None:
            pol_list = self.to_csv(policies)
            url = self.baseurl + f"smb-share-policies?names={pol_list}"
            msg = f"smb share policies: {pol_list}"
        else:
            url = self.baseurl + "smb-share-policies"
            msg = "smb share policies"
        
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get syslog servers
    def get_syslog_servers(self, syslog_names=None, dumpjson=False):
        if syslog_names is not None:
            syslog_list = self.to_csv(syslog_names)
            url = self.baseurl + f"syslog-servers?names={syslog_list}"
            msg = f"syslog servers: {syslog_list}"
        else:
            url = self.baseurl + f"syslog-servers"
            msg = f"syslog servers"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get connection key
    def get_connection_key(self, dumpjson=False):
        url = self.baseurl + "array-connections/connection-key"
        msg = "connection key"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get users quotas per file system
    def get_user_quotas(self, filesystem, dumpjson=False):
        url = self.baseurl + f"quotas/users?file_system_names={filesystem}"
        msg = f"{filesystem} user quotas"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get users file system usage
    def get_users_filesystem_usage(self, filesystem, uids=None, dumpjson=False):
        if uids is not None:
            uid_list = self.to_csv(uids)
            url = self.baseurl + f"usage/users?file_system_names={filesystem}&uids={uid_list}"
            msg = f"{filesystem} usage for UIDs: {uid_list}"
        else:
            url = self.baseurl + f"usage/users?file_system_names={filesystem}"
            msg = f"{filesystem} usage by UIDs"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get alert watchers
    def get_alert_watchers(self, watchers=None, dumpjson=False):
        if watchers is not None:
            watcher_list = self.to_csv(watchers)
            url = self.baseurl + f"alert-watchers?names={watcher_list}"
            msg = f"alert watchers: {watcher_list}"
        else:
            url = self.baseurl + "alert-watchers"
            msg = f"alert watchers"

        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get smtp servers
    def get_smtp_servers(self, dumpjson=False):
        url = self.baseurl + "smtp-servers"
        msg = f"smtp servers"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Get quotas settings
    def get_quotas_settings(self, dumpjson=False):
        url = self.baseurl + "quotas/settings"
        msg = f"quotas settings"
        data = self.api_request("get", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

 
    ########################
    ### POST API Section ###
    ########################


    # Post factory reset token
    def post_factory_reset_token(self, dumpjson=False):
        url = self.baseurl + "arrays/factory-reset-token"
        msg = "FACTORY RESET TOKEN"
        data = self.api_request("post", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Post a filesystem (default NFS)
    def post_filesystem(self, filesystem, payload, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}&default_exports=nfs"
        msg = f"filesystem: {filesystem}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post an object store account
    def post_object_store_account(self, account, payload, dumpjson=False):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)

    # Post a bucket
    def post_bucket(self, bucket, payload, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post a bucket replica link (ENDPOINT BROKEN)
    def post_bucket_replica_link(self, bucket, remote_credential, payload, dumpjson=False):
        url = self.baseurl + f"bucket-replica-links?local_bucket_names={bucket}&remote_bucket_names={bucket}&remote_credentials_names={remote_credential}"
        msg = f"bucket replica link: {bucket} with remote credential: {remote_credential}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post an object store user
    def post_object_store_user(self, user, dumpjson=False):
        url = self.baseurl + f"object-store-users?names={user}&full_access=true"
        msg = f"object store user: {user}"
        data = self.api_request("post", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post an object store access key (Secret key shown once in response)
    def post_object_store_access_key(self, user, payload, dumpjson=False):
        url = self.baseurl + "object-store-access-keys"
        msg = f"object store access key: {user}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post an object store remote credential (formatted <remote-name>/<credentials-name>)
    def post_object_store_remote_credential(self, credential_name, payload, dumpjson=False):
        url = self.baseurl + f"object-store-remote-credentials?names={credential_name}"
        msg = f"object store remote credential: {credential_name}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post a subnet
    def post_subnet(self, subnet, payload, dumpjson=False):
        url = self.baseurl + f"subnets?names={subnet}"
        msg = f"subnet: {subnet}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)

    # Post a network interface
    def post_interface(self, interface, payload, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)

    # Post a filesystem replica link (Replica Link ID required)
    def post_filesystem_replica_link(self, filesystem, remote_array, payload, dumpjson=False):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={filesystem}&remote_file_system_names={filesystem}&remote_names={remote_array}"
        msg = f"filesystem replica link: {filesystem}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post a filesystem snapshot
    def post_filesystem_snapshot(self, filesystem, snapshot, replicate=True, dumpjson=False):
        if replicate:
            url = self.baseurl + f"file-system-snapshots?source_names={filesystem}&send=true"
        else:
            url = self.baseurl + f"file-system-snapshots?source_names={filesystem}"
        msg = f"filesytem snapshot: {snapshot} for {filesystem}"
        data = self.api_request("post", url, msg, payload={"suffix":snapshot})
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post snapshot scheduling policy to a filesystem
    def post_snapshot_policy_to_filesystem(self, policy, filesystem, dumpjson=False):
        url = self.baseurl + f"file-systems/policies?member_names={filesystem}&policy_names={policy}"
        msg = f"snapshot policy {policy} to {filesystem}"
        data = self.api_request("post", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Post snapshot policy
    def post_snapshot_policy(self, policy, payload, dumpjson=False):
        url = self.baseurl + f"policies?names={policy}"
        msg = f"filesystem snapshot policies: {policy}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Post NFS export policy
    def post_nfs_export_policy(self, policy, payload, dumpjson=False):
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"NFS export policiy: {policy}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Post syslog server
    def post_syslog_server(self, syslog_name, uri, dumpjson=False):
        url = self.baseurl + f"syslog-servers?names={syslog_name}"
        msg = f"syslog server: {syslog_name}"
        data = self.api_request("post", url, msg, payload={"uri": uri})
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Post connection key
    def post_connection_key(self, dumpjson=False):
        url = self.baseurl + "array-connections/connection-key"
        msg = "connection key"
        data = self.api_request("post", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Post array connection 
    def post_array_connection(self, payload, dumpjson=False):
        url = self.baseurl + "array-connections"
        msg = "array connection"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Post certificate
    def post_certificate(self, certificate_name, payload, dumpjson=False):
        url = self.baseurl + f"certificates?names={certificate_name}"
        msg = f"certifcate: {certificate_name}"
        data = self.api_request("post", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Post certificate to a certificate group
    def post_certificate_to_group(self, certificate, group, dumpjson=False):
        url = self.baseurl + f"certificate-groups/certificates?certificate_names={certificate}&certificate_group_names={group}"
        msg = f"group/certificate: {group}/{certificate}"
        data = self.api_request("post", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    

    #########################
    ### PATCH API Section ###
    #########################
        
        
    # Patch a filesystem
    def patch_filesystem(self, filesystem, payload, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}"
        if payload.get("requested_promotion_state") == "demoted":
            url += "&discard_non_snapshotted_data=true"
        msg = f"filesystem: {filesystem}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    def patch_nfs_export_policy(self, policy, payload, dumpjson=False):
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"NFS export policy: {policy}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
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
            data = self.api_request("patch", url, msg, payload=payload)
            return self.parse_data(data, dumpjson=dumpjson)

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
        data = self.api_request("patch", url, msg, payload=rules)
        return self.parse_data(data, dumpjson=dumpjson)


    # Patch a network interface
    def patch_interface(self, interface, payload, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)

    # Patch a snapshot
    def patch_filesystem_snapshot(self, snapshot, payload, dumpjson=False):
        url = self.baseurl + f"file-system-snapshots?names={snapshot}"
        if payload["destroyed"] == True:
            url = url + "&latest_replica=True"
        msg = f"filesystem snapshot: {snapshot}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Patch a bucket
    def patch_bucket(self, bucket, payload, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"filesystem bucket: {bucket}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch directory services
    def patch_directory_services(self, name, payload, dumpjson=False):
        url = self.baseurl + f"directory-services?names={name}"
        msg = f"directory service: {name}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch directory service role
    def patch_directory_service_role(self, role_name, payload, dumpjson=False):
        url = self.baseurl + f"directory-services/roles?role_names={role_name}"
        msg = f"directory service role: {role_name}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch DNS
    def patch_dns(self, dns, payload, dumpjson=False):
        url = self.baseurl + f"dns?names={dns}"
        msg = f"DNS: {dns}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch SMTP
    def patch_smtp(self, payload, dumpjson=False):
        url = self.baseurl + f"smtp-servers"
        msg = "SMTP"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch quota settings
    def patch_quotas_settings(self, payload, dumpjson=False):
        url = self.baseurl + f"quotas/settings"
        msg = "quotas settings"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch array configurations
    def patch_array_configurations(self, payload, dumpjson=False):
        url = self.baseurl + f"arrays"
        msg = "array configurations"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Patch array connection
    def patch_array_connection(self, remote_name, payload, dumpjson=False):
        url = self.baseurl + f"array-connections?remote_names={remote_name}"
        msg = f"array connection: {remote_name}"
        data = self.api_request("patch", url, msg, payload=payload)
        return self.parse_data(data, dumpjson=dumpjson)


    ##########################
    ### DELETE API Section ###
    ##########################
    

    # Delete factory reset token
    def delete_factory_reset_tokens(self, dumpjson=False):
        url = self.baseurl + "arrays/factory-reset-token"
        msg = "FACTORY RESET TOKEN"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete a filesytem
    def delete_filesystem(self, filesystem, dumpjson=False):
        url = self.baseurl + f"file-systems?names={filesystem}"
        msg = f"filesystem: {filesystem}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete a bucket
    def delete_bucket(self, bucket, dumpjson=False):
        url = self.baseurl + f"buckets?names={bucket}"
        msg = f"bucket: {bucket}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete an object store user
    def delete_object_store_user(self, object_user, dumpjson=False):
        url = self.baseurl + f"object-store-users?names={object_user}"
        msg = f"object store user: {object_user}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete an object store access key
    def delete_object_store_access_key(self, access_key, dumpjson=False):
        url = self.baseurl + f"object-store-access-keys?names={access_key}"
        msg = f"access key: {access_key}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete an object store remote credential
    def delete_object_store_remote_credential(self, credential_name, dumpjson=False):
        url = self.baseurl + f"object-store-remote-credentials?names={credential_name}"
        msg = f"credential name: {credential_name}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete an object store account
    def delete_object_store_account(self, account, dumpjson=False):
        url = self.baseurl + f"object-store-accounts?names={account}"
        msg = f"object store account: {account}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete a bucket replica link
    def delete_bucket_replica_link(self, bucket, remote_name, dumpjson=False):
        url = self.baseurl + f"bucket-replica-links?local_bucket_names={bucket}&remote_bucket_names={bucket}&remote_names={remote_name}"
        msg = f"bucket replica link: {bucket}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete a filesystem replica link
    def delete_filesystem_replica_link(self, filesystem, remote_array, dumpjson=False):
        url = self.baseurl + f"file-system-replica-links?local_file_system_names={filesystem}&remote_file_system_names={filesystem}&remote_names={remote_array}&cancel_in_progress_transfers=true"
        msg = f"filesystem replica link: {filesystem}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)

    # Delete a filesystem snapshot
    def delete_filesystem_snapshot(self, snapshot, dumpjson=False):
        url = self.baseurl + f"file-system-snapshots?names={snapshot}"
        msg = f"snapshot: {snapshot}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete snapshot policies
    def delete_snapshot_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"policies?names={policy}"
        msg = f"snapshot policy: {policy}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete a NFS export policy
    def delete_nfs_export_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"nfs-export-policies?names={policy}"
        msg = f"NFS export policy: {policy}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete a SMB client policy
    def delete_smb_client_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"smb-client-policies?names={policy}"
        msg = f"SMB client policy: {policy}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete a SMB client policy
    def delete_smb_share_policy(self, policy, dumpjson=False):
        url = self.baseurl + f"smb-share-policies?names={policy}"
        msg = f"SMB share policy: {policy}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete a network interface
    def delete_interface(self, interface, dumpjson=False):
        url = self.baseurl + f"network-interfaces?names={interface}"
        msg = f"network interface: {interface}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete a subnet
    def delete_subnet(self, subnet, dumpjson=False):
        url = self.baseurl + f"subnets?names={subnet}"
        msg = f"subnet: {subnet}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
        
    # Delete an array connection
    def delete_array_connection(self, remote_name, dumpjson=False):
        url = self.baseurl + f"array-connections?remote_names={remote_name}"
        msg = f"array connection: {remote_name}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete syslog server
    def delete_syslog_server(self, syslog_server, dumpjson=False):
        url = self.baseurl + f"syslog-servers?names={syslog_server}"
        msg = f"syslog server: {syslog_server}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete certificate
    def delete_certifcate(self, certificate, dumpjson=False):
        url = self.baseurl + f"certificates?names={certificate}"
        msg = f"certificate: {certificate}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)
    
    # Delete alert watcher
    def delete_alert_watcher(self, watcher, dumpjson=False):
        url = self.baseurl + f"alert-watchers?names={watcher}"
        msg = f"watcher: {watcher}"
        data = self.api_request("delete", url, msg)
        return self.parse_data(data, dumpjson=dumpjson)