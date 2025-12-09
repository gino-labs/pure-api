#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
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
        if self.proceed_to_wipe("object replication", auto_wipe=auto_wipe):
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
            print("TODO: Wipe interfaces")
        else:
            return

    # Wipe subnets
    def wipe_subnets(self, auto_wipe=False):
        if self.proceed_to_wipe("subnets", auto_wipe=auto_wipe):
            print("TODO: Wipe subnets")
        else:
            return

    # Wipe NFS policies
    def wipe_nfs_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("nfs policies", auto_wipe=auto_wipe):
            print("TODO: Wipe NFS policies")
        else:
            return

    # Wipe SMB Policies
    def wipe_smb_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("smb policies", auto_wipe=auto_wipe):
            print("TODO: Wipe SMB policies")
        else:
            return

    # Wipe snapshot policies
    def wipe_snapshot_policies(self, auto_wipe=False):
        if self.proceed_to_wipe("snapshot policies", auto_wipe=auto_wipe):
            print("TODO: Wipe snapshot policies")
        else:
            return

    # CAUTION: Wipe file system data
    def wipe_filesystems(self, auto_wipe=False):
        if self.proceed_to_wipe("filesystems", auto_wipe=auto_wipe):
            print("TODO: Wipe filesystems")
        else:
            return

    # Wipe object store access keys
    def wipe_object_store_keys(self, auto_wipe=False):
        if self.proceed_to_wipe("object store access keys", auto_wipe=auto_wipe):
            print("TODO: Wipe object store access keys")
        else:
            return

    # Wipe object store users
    def wipe_object_store_users(self, auto_wipe=False):
        if self.proceed_to_wipe("object sotre users", auto_wipe=auto_wipe):
            print("TODO: Wipe object store users")
        else:
            return

    # CAUTION: Wipe object store buckets
    def wipe_object_store_buckets(self, auto_wipe=False):
        if self.proceed_to_wipe("object store buckets", auto_wipe=auto_wipe):
            print("TODO: Wipe object store buckets")
        else:
            return

    # Wipe object store accounts
    def wipe_object_store_accounts(self, auto_wipe=False):
        if self.proceed_to_wipe("object store accounts", auto_wipe=auto_wipe):
            print("TODO: Wipe object store accounts")
        else:
            return

    # Wipe syslog connections
    def wipe_syslog_connections(self, auto_wipe=False):
        if self.proceed_to_wipe("syslog server connections", auto_wipe=auto_wipe):
            print("TODO: Wipe syslog server connections")
        else:
            return

    # Wipe external certificates
    def wipe_external_certificates(self, auto_wipe=False):
        if self.proceed_to_wipe("external certificates", auto_wipe=auto_wipe):
            print("TODO: Wipe external certificates")
        else:
            return

    # Wipe directory services
    def wipe_directory_services(self, auto_wipe=False):
        if self.proceed_to_wipe("directory services", auto_wipe=auto_wipe):
            print("TODO: Wipe directory services")
        else:
            return

    # Wipe DNS configuration
    def wipe_dns(self, auto_wipe=False):
        if self.proceed_to_wipe("DNS", auto_wipe=auto_wipe):
            print("TODO: Wipe DNS")
        else:
            return

    # Wipe NTP configuration
    def wipe_ntp(self, auto_wipe=False):
        if self.proceed_to_wipe("NTP", auto_wipe=auto_wipe):
            print("TODO: Wipe NTP")
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
        self.wipe_smb_policies(auto_wipe=auto_wipe)
        self.wipe_snapshot_policies(auto_wipe=auto_wipe)
        self.wipe_filesystems(auto_wipe=auto_wipe)
        self.wipe_object_store_keys(auto_wipe=auto_wipe)
        self.wipe_object_store_users(auto_wipe=auto_wipe)
        self.wipe_object_store_buckets(auto_wipe=auto_wipe)
        self.wipe_object_store_accounts(auto_wipe=auto_wipe)
        
        if wipe_mgt_settings:
            self.wipe_syslog_connections(auto_wipe=auto_wipe)
            self.wipe_external_certificates(auto_wipe=auto_wipe)
            self.wipe_directory_services(auto_wipe=auto_wipe)
            self.wipe_dns(auto_wipe=auto_wipe)
            self.wipe_ntp(auto_wipe=auto_wipe)

        print("------------")
        self.logger.write_log(f"{self.fb_name}: has been WIPED.\n------------", show_output=True)

# Main
if __name__ == "__main__":
    # Wipe AZ Legacy FlashBlade
    az = [os.getenv("AZFB_NAME"),os.getenv("AZFB_DATA"),os.getenv("AZFB_MGT"),os.getenv("AZFB_TOKEN")]
    azwiper = FBWiper(*az)
    azwiper.wipe_all(auto_wipe=True)

    # Wipe CO Legacy FlashBlade
    co = [os.getenv("COFB_NAME"),os.getenv("COFB_DATA"),os.getenv("COFB_MGT"),os.getenv("COFB_TOKEN")]
    cowiper = FBWiper(*co)
    cowiper.wipe_all(auto_wipe=True)

    # Wipe VA Legacy FlashBlade
    va = [os.getenv("VAFB_NAME"),os.getenv("VAFB_DATA"),os.getenv("VAFB_MGT"),os.getenv("VAFB_TOKEN")]
    vawiper = FBWiper(*va)
    vawiper.wipe_all(auto_wipe=True)
    