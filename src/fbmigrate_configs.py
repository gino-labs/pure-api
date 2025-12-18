#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *
import ipaddress
import os


# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()


class ConfigMigrator:
    def __init__(self):
        self.rrc_site = rrc_site
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)
        self.logger = PureLog()
        self.watch = Stopwatch()
    
    def refresh_api_session(self):
        self.legacy = FlashBladeAPI(*pb1_vars)
        self.s200 = FlashBladeAPI(*pb2_vars)

    # Migrate export/import certificate from s200 to legacy
    def migrate_certificate(self):
        s200_global_cert = self.s200.get_certificates(certificates="global")
        legacy_certs = self.legacy.get_certificates()

        if isinstance(legacy_certs, dict):
            legacy_certs = [legacy_certs]

        if rrc_site.get_pb2_name() in [cert["name"] for cert in legacy_certs]:
            self.logger.write_log(f"External certificate {rrc_site.get_pb2_name()} already configured.", show_output=True)
        else:
            try:
                payload = {
                    "certificate": s200_global_cert["certificate"],
                    "certificate_type": "external",
                    "intermediate_certificate": s200_global_cert["intermediate_certificate"],
                }
                self.legacy.post_certificate(rrc_site.get_pb2_name(), payload)
            except ApiError as e:
                e.check_details()
        
        cert_group = self.legacy.get_certificate_group_members("_default_replication_certs")
        pb2_cert = rrc_site.get_pb2_name()
        
        if isinstance(cert_group, dict) and cert_group["member"]["name"] == pb2_cert:
            self.logger.write_log(f"Certificate {pb2_cert} in _default_replication_certs already configured.", show_output=True)
        elif cert_group and pb2_cert in [cert["member"]["name"] for cert in cert_group]:
            self.logger.write_log(f"Certificate {pb2_cert} in _default_replication_certs already configured.", show_output=True)
        else:
            try:
                self.legacy.post_certificate_to_group(rrc_site.get_pb2_name(), "_default_replication_certs")
            except ApiError as e:
                e.check_details()
        
    # Migrate directory services besides bind password, and leave disabled
    def migrate_directory_service(self):
        dir_svc = self.legacy.get_directory_services()
        if isinstance(dir_svc, list):
            dir_svc = dir_svc[0]

        payload = {
            "base_dn": dir_svc["base_dn"],
            "bind_user": dir_svc["bind_user"],
            "uris": dir_svc["uris"],
            "enabled": False
        }

        try:
            self.s200.patch_directory_services(dir_svc["name"], payload=payload)
        except ApiError as e:
            e.check_details()

    # Migrate directory service roles
    def migrate_directory_service_roles(self):
        dir_svc_roles = self.legacy.get_directory_service_roles()

        if not isinstance(dir_svc_roles, list):
            dir_svc_roles = [dir_svc_roles]

        for role in dir_svc_roles:
            try:
                payload = {
                    "role": { "name": role["role"]["name"] },
                    "group": role["group"],
                    "group_base": role["group_base"]
                }
                self.s200.patch_directory_service_role(role["role"]["name"], payload=payload)
            except ApiError as e:
                e.check_details()

    
    # Migrate Snapshot policies
    def migrate_snapshot_polices(self):
        legacy_snapshot_polices = self.legacy.get_snapshot_policies()
        s200_snapshot_policies = [pol["name"] for pol in self.s200.get_snapshot_policies()]

        for pol in legacy_snapshot_polices:
            if pol["name"] in s200_snapshot_policies:
                self.logger.write_log(f"Snapshot policy {pol['name']} already configured.", show_output=True)
            elif pol["name"] == "5_mins":
                continue
            else:
                payload = {
                    "name": pol["name"],
                    "enabled": pol["enabled"],
                    "rules": pol["rules"]
                }
                try:
                    self.s200.post_snapshot_policy(pol["name"], payload)
                except ApiError as e:
                    e.check_details()
    
    # Configure 5_mins snapshot policy for replication
    def configure_replication_snapshot_policy(self):
        policies = [pol["name"] for pol in self.legacy.get_snapshot_policies()]

        if "5_mins" in policies:
            self.logger.write_log("5 mins replication policy already configured", show_output=True)
        else:
            try:
                payload = {
                    "name": "5_mins",
                    "enabled": True,
                    "rules": [
                        {
                            "every": 300000,
                            "keep_for": 3600000
                        }
                    ]
                }
                self.legacy.post_snapshot_policy("5_mins", payload)
            except ApiError as e:
                e.check_details()


    # Create replication subnet/interface
    def configure_replication_net(self):
        legacy_subnets = [sub["name"] for sub in self.legacy.get_subnets()]
        s200_subnets = [sub["name"] for sub in self.s200.get_subnets()]

        subnet_payload = {
            "gateway": "172.20.0.1",
            "link_aggregation_group": {"name": "uplink"},
            "mtu": 9000,
            "prefix": "172.20.0.0/28",
            "vlan": 400
        }

        if "replication-subnet" in legacy_subnets:
            self.logger.write_log(f"Replication subnet for legacy already configured.", show_output=True)
        else:
            try:
                self.legacy.post_subnet("replication-subnet", subnet_payload)
            except ApiError as e:
                e.check_details()

        if "replication-subnet" in s200_subnets:
            self.logger.write_log(f"Replication subnet for s200 already configured.", show_output=True)
        else:
            try:
                self.s200.post_subnet("replication-subnet", subnet_payload)
            except ApiError as e:
                e.check_details()

        
        legacy_interfaces = [iface["name"] for iface in self.legacy.get_interfaces()]
        s200_interfaces = [iface["name"] for iface in self.s200.get_interfaces()]

        if "replication-interface" in legacy_interfaces:
            self.logger.write_log("Replication interface for legacy already configured.", show_output=True)
        else:      
            try:
                legacy_iface_payload = {
                    "address": rrc_site.get_pb1_replication_ip(),
                    "services": ["replication"],
                    "type": "vip"
                }  
                self.legacy.post_interface("replication-interface", legacy_iface_payload)
            except ApiError as e:
                e.check_details()

        if "replication-interface" in s200_interfaces:
            self.logger.write_log("Replication interface for s200 already configured.", show_output=True)
        else:
            try:
                s200_iface_payload = {
                    "address": rrc_site.get_pb2_replication_ip(),
                    "services": ["replication"],
                    "type": "vip"
                }
                self.s200.post_interface("replication-interface", s200_iface_payload)
            except ApiError as e:
                e.check_details()

    # Migrate array connections
    def configure_array_connection(self):
        legacy_array_conn = self.legacy.get_array_connections()

        if legacy_array_conn and rrc_site.get_pb2_name() == legacy_array_conn["remote"]["name"]:
            self.logger.write_log(f"Remote array connection to {legacy_array_conn['remote']['name']} already configured.", show_output=True)
        else:
            try:
                # Get/Post connection key from s200
                key_data = self.s200.post_connection_key()

                conn_key = key_data["connection_key"]

                os.makedirs(".secrets", exist_ok=True)
                with open(".secrets/conn_key.txt", "w") as f:
                    f.write(conn_key)

                # Post new array connection with s200 connection key
                payload = {
                    "encrypted": False,
                    "management_address": rrc_site.get_pb2_mgt_host(ip_addr=True),
                    "replication_addresses": [rrc_site.get_pb2_replication_ip()],
                    "connection_key": conn_key
                }
                self.legacy.post_array_connection(payload)
                
                s200_array_conns = self.s200.get_array_connections()

                if s200_array_conns and s200_array_conns["replication_address"] != rrc_site.get_pb1_replication_ip():
                    remote_name = rrc_site.get_pb1_name()
                    replica_patch = {"replication_address": rrc_site.get_pb1_replication_ip()}
                    self.s200.patch_array_connection(remote_name, replica_patch)
                else:
                    self.logger.write_log(f"Remote replication address to {rrc_site.get_pb1_name()} already configured.", show_output=True)
            except ApiError as e:
                e.check_details()

    # Migrate subnets, verify name, vlan, subnet prefix
    def migrate_subnets(self):
        legacy_subnets = self.legacy.get_subnets()
        s200_subnets = self.s200.get_subnets()

        # Store existing S200 subnet details to not recreate overlapping
        s200_sub_details = {
            "s200_subnames": [],
            "s200_prefixes": [],
            "s200_vlans": []
        }   
        if s200_subnets:
            if isinstance(s200_subnets, dict):
                s200_sub_details["s200_subnames"].append(s200_subnets["name"])
                s200_sub_details["s200_prefixes"].append(s200_subnets["prefix"])
                s200_sub_details["s200_vlans"].append(s200_subnets["vlan"])
            else:
                for sub in s200_subnets:
                    s200_sub_details["s200_subnames"].append(sub["name"])
                    s200_sub_details["s200_prefixes"].append(sub["prefix"])
                    s200_sub_details["s200_vlans"].append(sub["vlan"])

        # For each subnet on legacy post subnet to s200
        if legacy_subnets:
            if isinstance(legacy_subnets, dict):
                legacy_subnets = [legacy_subnets]
            s200_subnames = s200_sub_details["s200_subnames"]
            s200_prefixes = s200_sub_details["s200_prefixes"]
            s200_vlans = s200_sub_details["s200_vlans"]
            
            for sub in legacy_subnets:
                # Skip if subnet name, prefix, or vlan already exist from s200 info gathered in s200_sub_details
                if sub["name"] in s200_subnames:
                    self.logger.write_log(f"Subnet with {sub['name']} already configured.", show_output=True)
                    continue
                if sub["prefix"] in s200_prefixes:
                    self.logger.write_log(f"Subnet with {sub['prefix']} already configured.", show_output=True)
                    continue
                if sub["vlan"] in s200_vlans:
                    self.logger.write_log(f"Subnet with {sub['vlan']} already configured.", show_output=True)
                    continue
                
                # Check services of subnet before posting
                sub_svcs = sub.get("services")
                if (sub.get("services") and ("data" in sub_svcs) and ("replication" not in sub_svcs)):
                    payload = {
                        "gateway": sub["gateway"],
                        "link_aggregation_group": {
                            "name": sub["link_aggregation_group"]["name"]
                        },
                        "mtu": sub["mtu"],
                        "prefix": sub["prefix"],
                        "vlan": sub["vlan"]
                    }
                    # Post subnets to s200
                    try:
                        self.s200.post_subnet(sub["name"], payload)
                    except ApiError as e:
                        e.check_details(show_code=True, show_context=True)

    # Migrate / configure main data interface
    def configure_data_interface(self):
        s200_ifaces = self.s200.get_interfaces()
            
        while True:
            subnet_match = False
            try:
                ip = input("Please enter IP for data interface: ")
                print()

                data_ip_configured = False
                for iface in s200_ifaces:
                    if ip == iface["address"]:
                        data_ip_configured = True
                        break
                
                if data_ip_configured:
                    self.logger.write_log(f"Data ip {iface['address']} already configured.", show_output=True)
                    break

                ip = ipaddress.ip_address(ip)

                payload = {
                    "address": str(ip),
                    "services": ["data"],
                    "type": "vip"
                }

                # Default iface name or configure a subnet based one
                iface_name = "migration-interface"
                for sub in self.s200.get_subnets():
                    net = ipaddress.ip_network(sub["prefix"])
                    if ip in net:
                        if "subnet" in sub["name"]:
                            iface_name = sub["name"].replace("subnet", "interface")
                        else:
                            iface_name = sub["name"] + "-interface"
                        subnet_match = True
                        break
                
                if subnet_match:
                    self.s200.post_interface(iface_name, payload)
                    break
            except ApiError as e:
                e.check_details()

    # Migrate NFS rules
    def migrate_nfs_rules(self):
        legacy_filesystems = self.legacy.get_filesystems()

        for fs in legacy_filesystems:
            nfs_config = fs["nfs"]
            payload = {
                "nfs": {
                    "rules": nfs_config["rules"]
                }
            }
            self.s200.patch_filesystem(fs["name"], payload)
    
    # Migrate NFS export policies
    def migrate_nfs_policies(self):
        legacy_polices = self.legacy.get_nfs_export_policies()

        if isinstance(legacy_polices, dict):
            legacy_polices = list(legacy_polices)

        for pol in legacy_polices:
            rules = []
            for rule in pol["rules"]:
                rules.append(
                    {
                        "access": rule["access"],
                        "anongid": rule["anongid"],
                        "anonuid": rule["anonuid"],
                        "atime": rule["atime"],
                        "client": rule["client"],
                        "fileid_32bit": rule["fileid_32bit"],
                        "permission": rule["permission"],
                        "secure": rule["secure"],
                        "security": rule["security"],
                    }
                )
            payload = {
                "name": pol["name"],
                "enabled": pol["enabled"],
                "rules": rules
            }
            try:
                self.s200.post_nfs_export_policy(pol["name"], payload)
            except ApiError as e:
                if e.code == 1:
                    print(e.message + f" : {pol['name']}", end="\n\n")

    # Migrate syslog server configuration
    def migrate_syslog_server(self):
        legacy_syslog = self.legacy.get_syslog_servers()

        if isinstance(legacy_syslog, dict):
            self.s200.post_syslog_server(legacy_syslog["name"], legacy_syslog["uri"])
        else:
            for syslog in legacy_syslog:
                self.s200.post_syslog_server(syslog["name"], syslog["uri"])


# Main
if __name__ == "__main__":
    # Configuration Migrator instance
    cfg_migrator = ConfigMigrator()

    # Congifuration migration operations
    cfg_migrator.migrate_certificate()
    cfg_migrator.migrate_directory_service()
    cfg_migrator.migrate_directory_service_roles()
    cfg_migrator.migrate_snapshot_polices()
    cfg_migrator.configure_replication_snapshot_policy()
    cfg_migrator.configure_replication_net()
    cfg_migrator.configure_array_connection()
    cfg_migrator.migrate_subnets()
    cfg_migrator.configure_data_interface()
    
