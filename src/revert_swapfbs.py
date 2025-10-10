#!/usr/bin/env python3
from purefb_api import *
from purefb_log import *

# PureLog Instance
logger = PureLog()

# Stopwatch Instance
watch = Stopwatch()

# Site Variables
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# FlashBlade API Instances
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)


# Using logs/pure_configs/legacy_filesystems.json configure Legacy file systems to original state
legacy_fs_config = "legacy_filesystems.json"
logger.write_log(f"Loading original file system configurations for Legacy FlashBlade. (logs/pure_configs/{legacy_fs_config})", show_output=True)
original_legacy_filesystems = logger.load_config(legacy_fs_config)

for fs in original_legacy_filesystems:
    try:
        payload = {
            "nfs": {
                "v3_enabled": fs["nfs"]["v3_enabled"],
                "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
            },
            "requested_promotion_state": fs["requested_promotion_state"],
            "writable": fs["writable"]
        }
        legacy.patch_filesystem(fs["name"], payload)
    except ApiError as e:
        legacy.patch_filesystem(fs["name"], {"writable": True})
        

# Using logs/pure_configs/s200_filesystems.json configure S200 file systems to original state
s200_fs_config = "s200_filesystems.json"
logger.write_log(f"Loading original file system configurations for S200 FlashBlade. (logs/pure_configs/{s200_fs_config})", show_output=True)
original_s200_filesystems = logger.load_config(s200_fs_config)

for fs in original_s200_filesystems:
    try:
        payload = {
            "nfs": {
                "v3_enabled": fs["nfs"]["v3_enabled"],
                "v4_1_enabled": fs["nfs"]["v4_1_enabled"],
            },
            "requested_promotion_state": fs["requested_promotion_state"],
            "writable": fs["writable"]
        }
        s200.patch_filesystem(fs["name"], payload)
    except ApiError as e:
        s200.patch_filesystem(fs["name"], {"writable": False})


# Using logs/pure_configs/legacy_interfaces.json configure Legacy network interfaces to original state
legacy_if_config = "legacy_interfaces.json"
logger.write_log(f"Loading original network interface configurations for Legacy FlashBlade. (logs/pure_configs/{legacy_if_config})", show_output=True)
original_legacy_interfaces = logger.load_config(legacy_if_config)

for iface in legacy.get_interfaces():
    if ("data" in iface["services"]) and ("replication" not in iface["services"]):
        legacy.delete_interface(iface["name"])

for iface in original_legacy_interfaces:
    services = iface["services"]
    if ("data" in iface["services"]) and ("replication" not in iface["services"]):
        payload = {"address": iface["address"], "services": iface["services"], "type": "vip"}
        legacy.post_interface("iface_name")


# Using logs/pure_configs/s200_interfaces.json configure S200 network interfaces to original state
s200_if_config = "s200_interfaces.json"
logger.write_log(f"Loading original network interface configurations for S200 FlashBlade. (logs/pure_configs/{s200_if_config})", show_output=True)
original_s200_interfaces = logger.load_config(s200_if_config)

for iface in s200.get_interfaces():
    if ("data" in iface["services"]) and ("replication" not in iface["services"]):
        s200.delete_interface(iface["name"])

for iface in original_s200_interfaces:
    services = iface["services"]
    if ("data" in iface["services"]) and ("replication" not in iface["services"]):
        payload = {"address": iface["address"], "services": iface["services"], "type": "vip"}
        s200.post_interface("iface_name")

# Re-establish file repliation links where possible

# Re-establish object replication links where possible