from everpure.flashblade.api.resources.common import ApiSession, ApiError

class FBPost:
    def __init__(self, session: ApiSession, verify=False):
        self.session = session
        self.session.verify = verify

    def post_request(self, endpoint: str, params=None, json=None, only_items=True):
        url = f"{self.session.baseurl}/{endpoint}"
        response = self.session.post(url, params=params, json=json)
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
    
    def post_array_connections(self, json=None, **params):
        return self.parsed_response(self.post_request("array-connections", json=json, params=params))
          
    def post_bucket_replica_links(self, names: str, remote_credential_names: str, json=None, **params):
        params["local_bucket_names"] = names
        params["remote_bucket_names"] = names
        params["remote_credential_names"] = remote_credential_names
        return self.parsed_response(self.post_request("bucket-replica-links", json=json, params=params))
                
    def post_buckets(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("buckets", json=json, params=params))
    
    def post_certificates(self, names, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("certificates", json=json, params=params))
    
    def post_certificates_to_groups(self, certificate_names: str, certificate_group_names: str, json=None, **params):
        params["certificate_names"] = certificate_names
        params["certificate_group_names"] = certificate_group_names
        return self.parsed_response(self.post_request("certificate-groups/certificates", json=json, params=params))
           
    def post_connection_key(self):
        return self.parsed_response(self.post_request("array-connections/connection-key"))
        
    def post_filesystem_policies(self, filesystem_names: str, policy_names: str, json=None, **params):
        params["member_names"] = filesystem_names
        params["policy_names"] = policy_names
        return self.parsed_response(self.post_request("file-systems/policies", json=json, params=params))
        
    def post_filesystem_replica_links(self, names: str, remote_names: str, json=None, **params):
        params["local_file_system_names"] = names
        params["remote_file_system_names"] = names
        params["remote_names"] = remote_names
        return self.parsed_response(self.post_request("file-system-replica-links", json=json, params=params))
          
    def post_filesystem_snapshots(self, names: str, replication=True, json=None, **params):
        # Default to replication for most cases
        if replication:
            params["source_names"] = names
            params["send"] = "true"
        else:
            params["names"] = names
        return self.parsed_response(self.post_request("file-system-snapshots", json=json, params=params))
                    
    def post_filesystems(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("file-systems", json=json, params=params))
            
    def post_nfs_export_policies(self, names, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("nfs-export-policies", json=json, params=params))
            
    def post_network_interfaces(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("network-interfaces", json=json, params=params))
                
    def post_object_store_access_keys(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("object-store-access-keys", json=json, params=params)   )
        
    def post_object_store_accounts(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("object-store-accounts", json=json, params=params))
 
    def post_object_store_users(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("object-store-users", json=json, params=params))

    def post_object_store_remote_credentials(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("object-store-remote-credentials", json=json, params=params))
    
    def post_policies(self, names, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("policies", json=json, params=params))
        
    def post_subnets(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("subnets", json=json, params=params)  )

    def post_syslog_servers(self, names, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.post_request("syslog-servers", json=json, params=params) )
        