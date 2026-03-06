from _common import ApiSession

class FBGet:
    def __init__(self, session: ApiSession, verify=False):
        self.session = session
        self.session.verify = verify

    def _request(self, endpoint, params=None, only_items=True):
        url = f"{self.session.baseurl}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        if only_items:
            return response.json()["items"]
        else:
            return response.json()
    
    def get_filesystems(self, **params):
        return self._request("file-systems", params=params)
        
    def get_object_store_accounts(self, **params):
        return self._request("object-store-accounts", params=params)
        
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

