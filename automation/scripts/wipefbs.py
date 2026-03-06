#!/usr/bin/env python3
from purefb_api import *
from util.pure_logging import *
import os

# FlashBlade Wiper Class
class FBWiper:
    def __init__(self, fb_name, fb_data, fb_mgt, fb_token):
        self.fb = FlashBladeAPI(fb_data, fb_mgt, fb_token)
        self.fb_name = fb_name
        self.logger = PureLog()

    # Safe Stop: Ask for confirmation before proceeding to wipe asset
    def proceed_to_wipe(self, asset, auto_wipe=False):
        if auto_wipe:
            return True
        else:
            choice = input(f"{self.fb_name}: Are you sure you want to wipe {asset}? (y/n) ")
            while choice.lower() not in ('y', 'n'):
                choice = input("Invalid Input. Please enter 'y' or 'n' ")
            
            if choice.lower() == 'y':
                return True
            else: 
                return False

    # Wipe file replication links
    def wipe_file_replication(self, auto_wipe=False):
        if self.proceed_to_wipe("file replication", auto_wipe=auto_wipe):
            links = self.fb.get_filesystem_replica_links()
            if links:
                for link in links:
                    self.fb.delete_filesystem_replica_link(link["local_file_system"]["name"], link["remote"]["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: file replication links already wiped.", show_output=True)
        else:
            return

    # Wipe object replication links
    def wipe_object_replication(self, auto_wipe=False):
        if self.proceed_to_wipe("object replication", auto_wipe=auto_wipe):
            links = self.fb.get_bucket_replia_links()
            if links:
                for link in links:
                    self.fb.delete_bucket_replica_link(link["local_bucket"]["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: bucket replication links already wiped.", show_output=True)
        else:
            return
        
    # Wipe object store remote credentials
    def wipe_object_store_remote_credentials(self, auto_wipe=False):
        if self.proceed_to_wipe("object remote credentials", auto_wipe=auto_wipe):
            creds = self.fb.get_object_store_remote_credentials()
            if creds:
                for cred in creds:
                    self.fb.delete_object_store_remote_credential(cred["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: bucket remote credentials already wiped.", show_output=True)
        else:
            return

    # Wipe data interfaces
    def wipe_interfaces(self, auto_wipe=False):
        if self.proceed_to_wipe("interfaces", auto_wipe=auto_wipe):
            # Only non management and support interfaces
            ifaces = [iface for iface in self.fb.get_interfaces() if "management" not in iface["services"] and "support" not in iface["services"]]
            if ifaces:
                for iface in ifaces:
                    self.fb.delete_interface(iface["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: data/replication interfaces already wiped.", show_output=True)
        else:
            return

    # Wipe subnets
    def wipe_subnets(self, auto_wipe=False):
        if self.proceed_to_wipe("subnets", auto_wipe=auto_wipe):
            # Only non management and support subnets
            subs = [sub for sub in self.fb.get_subnets() if "management" not in sub["services"] and "support" not in sub["services"]]
            if subs:
                for sub in subs:
                    self.fb.delete_subnet(sub["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: data/replication subnets already wiped.", show_output=True)
        else:
            return

    # Wipe NFS policies
    def wipe_nfs_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("NFS export policies", auto_wipe=auto_wipe):
            pols = self.fb.get_nfs_export_policies()
            if pols:
                for pol in pols:
                    self.fb.delete_nfs_export_policy(pol["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: NFS export policies already wiped.", show_output=True)
        else:
            return

    # Wipe SMB client policies
    def wipe_smb_client_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("smb client policies", auto_wipe=auto_wipe):
            pols = [pol for pol in self.fb.get_smb_client_policies() if "allow_everyone" not in pol["name"]]
            if pols:
                for pol in pols:
                    self.fb.delete_smb_client_policy(pol["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: SMB client policies already wiped.", show_output=True)
        else:
            return
        
    # Wipe SMB share policies
    def wipe_smb_share_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("smb share policies", auto_wipe=auto_wipe):
            pols = [pol for pol in self.fb.get_smb_share_policies() if "allow_everyone" not in pol["name"]]
            if pols:
                for pol in pols:
                    self.fb.delete_smb_share_policy(pol["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: SMB share policies already wiped.", show_output=True)
        else:
            return

    # Wipe snapshot policies
    def wipe_snapshot_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("snapshot policies", auto_wipe=auto_wipe):
            pols = self.fb.get_snapshot_policies()
            if pols:
                for pol in pols:
                    self.fb.delete_snapshot_policy(pol["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: snapshot policies already wiped.", show_output=True)
        else:
            return

    # CAUTION: Wipe file system data
    def wipe_filesystems(self, auto_wipe=False):
        if self.proceed_to_wipe("filesystems", auto_wipe=auto_wipe):
            filesystems = self.fb.get_filesystems()
            if filesystems:
                for fs in filesystems:
                    payload = {
                        "destroyed": True,
                        "http": { "enabled": False },
                        "nfs": { "v3_enabled": False, "v4_1_enabled": False},
                        "smb": { "enabled": False }
                    }
                    # Step 1. Patch
                    self.fb.patch_filesystem(fs["name"], payload)
                    # Step 2. Delete
                    self.fb.delete_filesystem(fs["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: filesystems already wiped.", show_output=True)
        else:
            return

    # Wipe object store access keys
    def wipe_object_store_keys(self, auto_wipe=False):
        if self.proceed_to_wipe("object store access keys", auto_wipe=auto_wipe):
            keys = self.fb.get_object_store_access_keys()
            if keys:
                for key in keys:
                    self.fb.delete_object_store_access_key(key["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: object store access keys already wiped.", show_output=True)
        else:
            return

    # Wipe object store users
    def wipe_object_store_users(self, auto_wipe=False):
        if self.proceed_to_wipe("object sotre users", auto_wipe=auto_wipe):
            users = self.fb.get_object_store_users()
            if users:
                for user in users:
                    self.fb.delete_object_store_user(user["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: object store users already wiped.", show_output=True)
        else:
            return

    # CAUTION: Wipe object store buckets
    def wipe_object_store_buckets(self, auto_wipe=False):
        if self.proceed_to_wipe("object store buckets", auto_wipe=auto_wipe):
            buckets = self.fb.get_buckets()
            if buckets:
                for bucket in buckets:
                    # Step 1. Patch
                    self.fb.patch_bucket(bucket["name"], {"destroyed": True})
                    # Step 2. Delete
                    self.fb.delete_bucket(bucket["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: object store buckets already wiped.", show_output=True)
        else:
            return

    # Wipe object store accounts
    def wipe_object_store_accounts(self, auto_wipe=False):
        if self.proceed_to_wipe("object store accounts", auto_wipe=auto_wipe):
            accts = self.fb.get_object_store_accounts()
            if accts:
                for acct in accts:
                    self.fb.delete_object_store_account(acct["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: object store accounts already wiped.", show_output=True)
        else:
            return

    # Wipe syslog connections
    def wipe_syslog_servers(self, auto_wipe=False):
        if self.proceed_to_wipe("syslog servers", auto_wipe=auto_wipe):
            log_srvs = self.fb.get_syslog_servers()
            if log_srvs:
                for srv in log_srvs:
                    self.fb.delete_syslog_server(srv["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: syslog servers already wiped.", show_output=True)
        else:
            return
    
    # Wipe external certificates
    def wipe_external_certificates(self, auto_wipe=False):
        if self.proceed_to_wipe("external certificates", auto_wipe=auto_wipe):
            ext_certs = [cert for cert in self.fb.get_certificates() if "external" == cert["certificate_type"]]
            if ext_certs:
                for cert in ext_certs:
                    self.fb.delete_certifcate(cert["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: external certificates already wiped.", show_output=True)
        else:
            return

    # Wipe alert watchers
    def wipe_alert_watchers(self, auto_wipe=False):
        if self.proceed_to_wipe("alert watchers", auto_wipe=auto_wipe):
            watchers = self.fb.get_alert_watchers()
            if watchers:
                for watcher in watchers:
                    self.fb.delete_alert_watcher(watcher["name"])
            else:
                self.logger.write_log(f"{self.fb_name}: alert watchers already wiped.", show_output=True)
        else:
            return
        
    # Wipe quotas settings
    def wipe_quotas_settings(self, auto_wipe=False):
        if self.proceed_to_wipe("quotas settings", auto_wipe=auto_wipe):
            qsets = [qset for qset in self.fb.get_quotas_settings() if qset["contact"] or qset["direct_notifications_enabled"]]
            if qsets:
                payload = {"contact": "", "direct_notifications_enabled": False}
                self.fb.patch_quotas_settings(payload)
            else:
                self.logger.write_log(f"{self.fb_name}: quotas settings already wiped.", show_output=True)
        else:
            return

    # Wipe directory service roles
    def wipe_directory_service_roles(self, auto_wipe=False):
        if self.proceed_to_wipe("directory service roles", auto_wipe=auto_wipe):
            roles = [role for role in self.fb.get_directory_service_roles() if role["group"] or role["group_base"]]
            if roles:
                payload = {"group": "", "group_base": ""}
                for role in roles:
                    self.fb.patch_directory_service_role(role["role"]["name"], payload)
            else:
                    self.logger.write_log(f"{self.fb_name}: directory service roles already wiped.", show_output=True)
        else:
            return
              
    # Wipe directory services
    def wipe_directory_services(self, auto_wipe=False):
        if self.proceed_to_wipe("directory services", auto_wipe=auto_wipe):
            dir_svcs = [svc for svc in self.fb.get_directory_services() if svc["base_dn"] or svc["bind_user"] or svc["bind_password"] or svc["enabled"]]
            if dir_svcs:
                payload = {
                    "base_dn": "",
                    "bind_password": "",
                    "bind_user": "",
                    "ca_certificate": {"name": None, "id": None},
                    "ca_certificate_group": {"name": None, "id": None},
                    "enabled": False,
                    "management": {"user_login_attribute": None, "user_object_class": None},
                    "nfs": {"nis_domains": [], "nis_servers": []},
                    "smb": {"join_ou": None},
                    "uris": []
                }
                for dir_svc in dir_svcs:
                    self.fb.patch_directory_services(dir_svc["name"], payload)
            else:
                self.logger.write_log(f"{self.fb_name}: directory services already wiped.", show_output=True)
        else:
            return

    # Wipe DNS configuration
    def wipe_dns(self, auto_wipe=False):
        if self.proceed_to_wipe("DNS configurations", auto_wipe=auto_wipe):
            dns_cfgs = [cfg for cfg in self.fb.get_dns() if cfg["domain"] != "local.arpa" or cfg["nameservers"] != []]
            if dns_cfgs:
                payload = {
                    "domain": "local.arpa",
                    "nameservers": []
                }
                for dns_cfg in dns_cfgs:
                    self.fb.patch_dns(dns_cfg["name"], payload)
            else:
                self.logger.write_log(f"{self.fb_name}: DNS configurations already wiped.", show_output=True)
        else:
            return
        
    # Wipe smtp servers
    def wipe_smtp_servers(self, auto_wipe=False):
        if self.proceed_to_wipe("smtp servers", auto_wipe=auto_wipe):
            smtp_srvs = [srv for srv in self.fb.get_smtp_servers() if srv["sender_domain"] != "local.arpa" or srv["relay_host"]]
            if smtp_srvs:
                payload = {
                    "sender_domain": "local.arpa",
                    "relay_host": ""
                }
                self.fb.patch_smtp(payload)
            else:
                self.logger.write_log(f"{self.fb_name}: SMTP configurations already wiped.", show_output=True)
        else:
            return

    # Wipe general array configurations
    def wipe_array_configurations(self, auto_wipe=False):
        if self.proceed_to_wipe("array configurations", auto_wipe=auto_wipe):
            array_cfg = [cfg for cfg in self.fb.get_array_configurations() if "flashblade" not in cfg["name"] or "Decommissioned: Legacy FlashBlade (DO NOT USE)" != cfg["banner"] or cfg["ntp_servers"] != [] or cfg["time_zone"] != "UTC"]
            if array_cfg:
                if "az" in self.fb_name:
                    num = "01"
                elif "co" in self.fb_name:
                    num = "02"
                else:
                    num = "03"
                payload = {
                    "name": "flashblade" + num,
                    "banner": "Decommissioned: Legacy FlashBlade (DO NOT USE)",
                    "ntp_servers": [],
                    "time_zone": "UTC"
                }
                self.fb.patch_array_configurations(payload)
            else:
                self.logger.write_log(f"{self.fb_name}: array configurations already wiped.", show_output=True)
        else:
            return
        
    # Generate a factory reset token
    def generate_factory_reset_token(self, recreate=False):   
        if recreate:
            self.logger.write_log("Recreating tokens...", show_output=True)
            self.fb.delete_factory_reset_tokens()
            tokens = []
        else:
            tokens = self.fb.get_factory_reset_tokens()

        if tokens:
            self.logger.write_log("Factory reset token already generated.", show_output=True)
            return
        else:
            choice = input("Would you like to generate a factory reset token? (y/n): ").lower()
            while choice not in ("y", "n"):
                choice = input("Please enter 'y' or 'n' for a factory reset token: ").lower()
            if choice == 'y':
                token_info = self.fb.post_factory_reset_token()
                self.logger.write_log(f"Writing token to .secrets/{self.fb_name}_factory_reset_token.json", show_output=True)
                with open(f".secrets/{self.fb_name}_factory_reset_token.json", "w") as f:
                    json.dump(token_info, f, indent=4)
            else:
                return

    # Wipe everything we can
    def wipe_all(self, wipe_mgt_settings=True, auto_wipe=False):
        self.wipe_file_replication(auto_wipe=auto_wipe)
        self.wipe_object_replication(auto_wipe=auto_wipe)
        self.wipe_object_store_remote_credentials(auto_wipe=auto_wipe)
        self.wipe_interfaces(auto_wipe=auto_wipe)
        self.wipe_subnets(auto_wipe=auto_wipe)
        self.wipe_nfs_policies(auto_wipe=auto_wipe)
        self.wipe_smb_client_policies(auto_wipe=auto_wipe)
        self.wipe_smb_share_policies(auto_wipe=auto_wipe)
        self.wipe_snapshot_policies(auto_wipe=auto_wipe)
        self.wipe_filesystems(auto_wipe=auto_wipe)
        self.wipe_object_store_keys(auto_wipe=auto_wipe)
        self.wipe_object_store_users(auto_wipe=auto_wipe)
        self.wipe_object_store_buckets(auto_wipe=auto_wipe)
        self.wipe_object_store_accounts(auto_wipe=auto_wipe)
        
        if wipe_mgt_settings:
            self.wipe_syslog_servers(auto_wipe=auto_wipe)
            self.wipe_external_certificates(auto_wipe=auto_wipe)
            self.wipe_alert_watchers(auto_wipe=auto_wipe)
            self.wipe_quotas_settings(auto_wipe=auto_wipe)
            self.wipe_directory_service_roles(auto_wipe=auto_wipe)
            self.wipe_directory_services(auto_wipe=auto_wipe)
            self.wipe_dns(auto_wipe=auto_wipe)
            self.wipe_smtp_servers(auto_wipe=auto_wipe)
            self.wipe_array_configurations(auto_wipe=auto_wipe)

        print("------------")
        self.logger.write_log(f"{self.fb_name}: has been WIPED.\n------------", show_output=True)

# Main
if __name__ == "__main__":
    # Wipe AZ Legacy FlashBlade
    az = [os.getenv("AZFB_NAME"),os.getenv("AZFB_DATA"),os.getenv("AZFB_MGT"),os.getenv("AZFB_TOKEN")]
    azwiper = FBWiper(*az)
    azwiper.wipe_all(auto_wipe=True)
    azwiper.generate_factory_reset_token(recreate=True)

    # Wipe CO Legacy FlashBlade
    co = [os.getenv("COFB_NAME"),os.getenv("COFB_DATA"),os.getenv("COFB_MGT"),os.getenv("COFB_TOKEN")]
    cowiper = FBWiper(*co)
    cowiper.wipe_all(auto_wipe=True)
    cowiper.generate_factory_reset_token(recreate=True)

    # Wipe VA Legacy FlashBlade
    va = [os.getenv("VAFB_NAME"),os.getenv("VAFB_DATA"),os.getenv("VAFB_MGT"),os.getenv("VAFB_TOKEN")]
    vawiper = FBWiper(*va)
    vawiper.wipe_all(auto_wipe=True)
    vawiper.generate_factory_reset_token(recreate=True)
    