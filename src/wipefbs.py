#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
import os

# FlashBlade Wiper Class
class FBWiper:
    def __init__(self, fb_inst, fb_name="FlashBlade"):
        self.fb = fb_inst
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
            print("TODO: Wipe file replication")
        else:
            return

    # Wipe object replication links
    def wipe_object_replication(self, auto_wipe=False):
        if self.proceed_to_wipe("object replication", auto_wipe=auto_wipe):
            print("TODO: Wipe object replication")
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

        self.logger.write_log(f"{self.fb_name}: configurations wiped.", show_output=True)

# Main
if __name__ == "__main__":
    # AZ Legacy
    azfb = {
        "name": os.getenv("AZFB_NAME"),
        "mgt": os.getenv("AZFB_MGT"),
        "data": os.getenv("AZFB_DATA"),
        "token": os.getenv("AZFB_TOKEN")
    }
    az = FlashBladeAPI(azfb["data"], azfb["mgt"], azfb["token"])

    # Wipe AZ Legacy FlashBlade
    azwiper = FBWiper(az, azfb["name"])
    azwiper.wipe_all(auto_wipe=True)

    # CO Legacy
    cofb = {
        "name": os.getenv("COFB_NAME"),
        "mgt": os.getenv("COFB_MGT"),
        "data": os.getenv("COFB_DATA"),
        "token": os.getenv("COFB_TOKEN")
    }
    co = FlashBladeAPI(cofb["data"], cofb["mgt"], cofb["token"])

    # Wipe CO Legacy FlashBlade
    cowiper = FBWiper(co, cofb["name"])
    cowiper.wipe_all(auto_wipe=True)

    # VA Legacy
    vafb = {
        "name": os.getenv("VAFB_NAME"),
        "mgt": os.getenv("VAFB_MGT"),
        "data": os.getenv("VAFB_DATA"),
        "token": os.getenv("VAFB_TOKEN")
    }
    va = FlashBladeAPI(vafb["data"], vafb["mgt"], vafb["token"])

    # Wipe VA Legacy FlashBlade
    vawiper = FBWiper(va, vafb["name"])
    vawiper.wipe_all(auto_wipe=True)
    