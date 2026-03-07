from everpure.flashblade.api.resources.common import ApiSession, ApiError

class FBGet:
    def __init__(self, session: ApiSession, verify=False):
        self.session = session
        self.session.verify = verify

    def get_request(self, endpoint, params=None):
        url = f"{self.session.baseurl}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response
    
    def parsed_response(self, response, only_items=True):
        data = response.json()

        if "errors" in data:
            err_code = data["errors"][0]["code"]
            err_context = data["errors"][0]["context"]
            err_message = data["errors"][0]["message"]
            raise ApiError(err_message, err_code, err_context)
        
        if only_items:
            return data["items"]
        else:
            return data
        
    def get_alert_watchers(self, **params):
        return self.parsed_response(self.get_request("alert-watchers", params=params))

    def get_array_connections(self, sub_resource=None, **params):
        ep = "array-conections" if not sub_resource else f"array-connections/{sub_resource}"
        return self.parsed_response(self.get_request(ep, params=params))
    
    def get_arrays(self, sub_resource=None, **params):
        ep = "arrays" if not sub_resource else f"arrays/{sub_resource}"
        return self.parsed_response(self.get_request(ep, params=params))

    def get_bucket_replica_links(self, **params):
        return self.parsed_response(self.get_request("bucket-replica-links", params=params))
                
    def get_buckets(self, **params):
        return self.parsed_response(self.get_request("buckets", params=params))
        
    def get_certificate_group_members(self, **params):
        return self.get_certificate_groups(sub_resource="certificates", params=params)
        
    def get_certificate_groups(self, sub_resource=None, **params):
        ep = "certificate-groups" if not sub_resource else f"certificate-groups/{sub_resource}"
        return self.parsed_response(self.get_request(ep, params=params))
    
    def get_certificates(self, **params):
        return self.parsed_response(self.get_request("certificates", params=params))
       
    def get_clients(self, **params):
        return self.get_arrays(sub_resource="clients/performance", params=params)
        
    def get_connection_key(self, **params):
        return self.get_array_connections(sub_resource="connection-key", params=params)
        
    def get_directory_services(self, sub_resource=None, **params):
        ep = "directory-services" if not sub_resource else f"directory-services/{sub_resource}"
        return self.parsed_response(self.get_request(ep, params=params))
        
    def get_dns(self, **params):
        return self.parsed_response(self.get_request("dns", params=params))
       
    def get_filesystem_replica_links(self, **params):
        return self.parsed_response(self.get_request("file-system-replica-links", params=params))
        
    def get_filesystem_snapshots(self, **params):
        return self.parsed_response(self.get_request("file-system-snapshots", params=params))
            
    def get_filesystems(self, sub_resource=None, **params):
        ep = "file-systems" if not sub_resource else f"file-systems/{sub_resource}"
        return self.parsed_response(self.get_request(ep, params=params))

    def get_object_store_access_keys(self, **params):
        return self.parsed_response(self.get_request("object-store-access-keys", params=params))
             
    def get_object_store_accounts(self, **params):
        return self.parsed_response(self.get_request("object-store-accounts", params=params))

    def get_object_store_remote_credentials(self, **params):
        return self.parsed_response(self.get_request("object-store-remote-credentials", params=params))
    
    def get_object_store_users(self, **params):
        return self.parsed_response(self.get_request("object-store-users", params))
        
    def get_network_interfaces(self, params):
        return self.parsed_response(self.get_request("network-interfaces", params=params))
    
    def get_nfs_export_policies(self, **params):
        return self.parsed_response(self.get_request("nfs-export-policies", params=params))
    
    def get_quotas_groups(self, **params):
        return self.parsed_response(self.get_request("quotas/groups", params=params)    )
    
    def get_quotas_settings(self, **params):
        return self.parsed_response(self.get_request("quotas/settings", params=params))
        
    def get_quotas_users(self, **params):
        return self.parsed_response(self.get_request("quotas/users", params=params))
       
    def get_roles(self, **params):
        return self.get_directory_services(sub_resource="roles", params=params)
        
    def get_smb_client_policies(self, **params):
        return self.parsed_response(self.get_request("smb-client-policies", params=params))
      
    def get_smb_share_policies(self, **params):
        return self.parsed_response(self.get_request("smb-share-policies", params=params))
        
    def get_smtp_servers(self, **params):
        return self.parsed_response(self.get_request("smtp-servers", params=params))
        
    def get_snapshot_policies(self, **params):
        return self.parsed_response(self.get_request("policies", params=params))
    
    def get_snapshot_policy_members(self, **params):
        return self.get_filesystems(sub_resource="policies", params=params)
           
    def get_subnets(self, **params):
        return self.parsed_response(self.get_request("subnets", params=params))

    def get_syslog_servers(self, **params):
        return self.parsed_response(self.get_request("syslog-servers", params=params))

    def get_usage_groups(self, **params):
        return self.parsed_response(self.get_request("usage/groups", params=params))
           
    def get_usage_users(self, **params):
        return self.parsed_response(self.get_request("usage/users", params=params))
    
