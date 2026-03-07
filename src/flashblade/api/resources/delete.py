from flashblade.api.resources.common import ApiSession, ApiError

class FBDelete:
    def __init__(self, session: ApiSession, verify=False):
        self.session = session
        self.session.verify = verify

    def delete_request(self, endpoint, params=None):
        url = f"{self.session.baseurl}/{endpoint}"
        response = self.session.delete(url, params=params)
        response.raise_for_status()
        try:
            data = response.json()
            if "errors" in data:
                err_code = data["errors"][0]["code"]
                err_context = data["errors"][0]["context"]
                err_message = data["errors"][0]["message"]
                raise ApiError(err_message, err_code, err_context)
        except ValueError:
            pass
        return response

    def delete_alert_watchers(self, names: str, **params):
        params["names"] = names
        return self.delete_request("alert-watchers", params=params)
            
    def delete_array_connections(self, remote_names: str, **params):
        params["remote_names"] = remote_names
        return self.delete_request("array-connections", params=params)
       
    def delete_bucket_replica_links(self, bucket_names: str, remote_names: str, **params):
        params["local_bucket_names"] = bucket_names
        params["remote_bucket_names"] = bucket_names
        params["remote_names"] = remote_names
        return self.delete_request("bucket-replica-links", params=params)

    def delete_buckets(self, names: str, **params):
        params["names"] = names
        return self.delete_request("buckets", params=params)
        
    def delete_certifcates(self, names: str, **params):
        params["names"] = names
        return self.delete_request("certificates", params=params)
    
    def delete_filesystem_replica_links(self, filesystem_names: str, remote_names: str, **params):
        # TODO: look into why this param was a default before, '&cancel_in_progress_transfers=true'
        params["local_file_system_names"] = filesystem_names
        params["remote_file_system_names"] = filesystem_names
        params["remote_names"] = remote_names
        return self.delete_request("file-system-replica-links", params=params)

    def delete_filesystem_snapshots(self, names: str, **params):
        params["names"] = names
        return self.delete_request("file-system-snapshots", params=params)
    
    def delete_filesystems(self, names: str, **params):
        params["names"] = names
        return self.delete_request("file-systems", params=params)
        
    def delete_network_interfaces(self, names: str, **params):
        params["names"] = names
        return self.delete_request("network-interfaces", params=params)
        
    def delete_nfs_export_policies(self, names: str, **params):
        params["names"] = names
        return self.delete_request("nfs-export-policies", params=params)
    
    def delete_object_store_access_keys(self, names: str, **params):
        params["names"] = names   
        return self.delete_request("object-store-access-keys", params=params)
        
    def delete_object_store_accounts(self, names: str, **params):
        params["names"] = names
        return self.delete_request("object-store-accounts", params=params)
    
    def delete_object_store_remote_credentials(self, names: str, **params):
        params["names"] = names
        return self.delete_request("object-store-remote-credentials", params=params)

    def delete_object_store_users(self, names: str, **params):
        params["names"] = names
        return self.delete_request("object-store-users", params=params)
    
    def delete_policies(self, names: str, **params):
        params["names"] = names
        return self.delete_request("policies", params=params)

    def delete_smb_client_policies(self, names: str, **params):
        params["names"] = names
        return self.delete_request("smb-client-policies", params=params)
    
    def delete_smb_share_policies(self, names: str, **params):
        params["names"] = names
        return self.delete_request("smb-share-policies", params=params)

    def delete_subnets(self, names: str, **params):
        params["names"] = names
        return self.delete_request("subnets", params=params)

    def delete_syslog_servers(self, names: str, **params):
        params["names"] = names
        return self.delete_request("syslog-servers", params=params)
