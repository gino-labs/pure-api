from flashblade.api.resources.common import ApiSession, ApiError

class FBPatch:
    def __init__(self, session: ApiSession, verify=False):
        self.session = session
        self.session.verify = verify

    def patch_request(self, endpoint, params=None):
        url = f"{self.session.baseurl}/{endpoint}"
        response = self.session.patch(url, params=params)
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
        
    def patch_array_connections(self, remote_names: str, json=None, **params):
        params["remote_names"] = remote_names
        return self.parsed_response(self.patch_request("array-connections", json=json, params=params))
    
    def patch_arrays(self, json: dict, **params):
        return self.parsed_response(self.patch_request("arrays", json=json, params=params))
            
    def patch_buckets(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.patch_request("buckets", json=json, params=params))
    
    def patch_directory_services(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.patch_request("directory-services", json=json, params=params))
        
    def patch_dns(self, names, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.patch_request("dns", json=json, params=params))
    
    def patch_filesystem_snapshots(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.patch_request("file-system-snapshots", json=json, params=params))

    def patch_filesystems(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.patch_request("file-systems", json=json, params=params))

    def patch_network_interfaces(self, names: str, json=None, **params):
        params["names"] = names
        return self.parsed_response(self.patch_request("network-interfaces", json=json, params=params))
        
    def patch_nfs_export_policies(self, names: str, json=None, **params):
        params["names"] = names       
        return self.parsed_response(self.patch_request("nfs-export-policies", json=json, params=params))
        
    def patch_quotas_settings(self, json: dict, **params):
        return self.parsed_response(self.patch_request("quotas/settings", json=json, params=params))

    def patch_roles(self, role_names: str, json=None, **params):
        params["role_names"] = role_names
        return self.parsed_response(self.patch_request("directory-services/roles", json=json, params=params))

    def patch_smtp_servers(self, json: dict, **params):
        return self.parsed_response(self.patch_request("smtp-servers", json=json, params=params))

