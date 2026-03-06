from purefb_log import *
from purefb_api import *

# Logger object for logs
logger = PureLog()

# Stopwatch for script runtimes
watch = Stopwatch()

# Site environment variables sourced from shell
rrc_site = SiteVars()
pb1_vars = rrc_site.get_pb1_vars()
pb2_vars = rrc_site.get_pb2_vars()

# Create API object instances of each array
legacy = FlashBladeAPI(*pb1_vars)
s200 = FlashBladeAPI(*pb2_vars)

# Helper function to compare list items from legacy and s200
def compare_lists(list1, list2, check_one=False):
    if check_one:
        diffs = list(set(list1) - set(list2))
    else:
        legacy_diffs = set(list1) - set(list2)
        s200_diffs = set(list2) - set(list1)

        diffs = {
            "unique_to_legacy": list(legacy_diffs or []),
            "unique_to_s200": list(s200_diffs or [])
        }
    return diffs

# Check file systems match, if not show differences
def check_file_systems():
    logger.write_log("Checking if file system names match between FBs.", show_output=True)

    legacy_filesystems = [fs["name"] for fs in legacy.get_filesystems()]
    s200_filesystems = [fs["name"] for fs in s200.get_filesystems()]

    diffs = compare_lists(legacy_filesystems, s200_filesystems)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique file systems found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique file systems found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs["unique_to_s200"] and not diffs["unique_to_legacy"]:
        logger.write_log("File system names match for both legacy and s200.")

# Check for non replication snapshot policies from legacy on s200 
def check_snapshot_policies():
    logger.write_log("Check if snapshot policies match between FBs.", show_output=True)

    legacy_policies = set([pol["name"] for pol in legacy.get_snapshot_policies() if "5_min" not in pol["name"]])
    s200_policies = set([pol["name"] for pol in s200.get_snapshot_policies() if "5_min" not in pol["name"]])

    diffs = compare_lists(legacy_policies, s200_policies)
    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique snapshot policy names found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique snapshot policy names found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs["unique_to_s200"] and not diffs["unique_to_legacy"]:
        logger.write_log("Snapshot policy names match for both legacy and s200.")

# Check that file systems on both legacy and s200 have same snapshot polices
def check_matching_attached_snapshot_policies():
    logger.write_log("Check if file systems have matching snapshot polices attached between FBs.", show_output=True)

    legacy_fs_attch_pols = legacy.get_snapshot_policy_members()
    s200_fs_attch_pols = s200.get_snapshot_policy_members()

    # Build out dictionary containing legacy policies and associated file system members
    legacy_policy_and_members = {}
    for fs_pol in legacy_fs_attch_pols:
        if fs_pol["policy"]["name"] not in legacy_policy_and_members:
            legacy_policy_and_members[fs_pol["policy"]["name"]] = []
        legacy_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for Legacy...", jsondata=legacy_policy_and_members)

    # Build out dictionary containing s200 policies and associated file system members
    s200_policy_and_members = {}
    for fs_pol in s200_fs_attch_pols:
        if fs_pol["policy"]["name"] not in s200_policy_and_members:
            s200_policy_and_members[fs_pol["policy"]["name"]] = []
        s200_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for S200...", jsondata=s200_policy_and_members)

    # Compare policies and members from each each 
    for pol, member_list in legacy_policy_and_members.items():
        if pol not in s200_policy_and_members:
            continue
        legacy_members = member_list
        s200_members = s200_policy_and_members[pol]

        diffs = compare_lists(legacy_members, s200_members, check_one=True)

        if diffs:
            logger.write_log(f"Attached snapshot policy \"{pol}\" has MISSING filesystem members on s200.", jsondata=diffs, show_output=True)
        else:
            logger.write_log(f"Snapshot policy {pol} attched to same file systems on both FBs.", show_output=True)

# Check subnets names and vlans match for data interfaces
def check_subnets():
    logger.write_log("Check if subnet names match between FBs", show_output=True)

    legacy_subs = [sub["name"] for sub in legacy.get_subnets()]
    s200_subs = [sub["name"] for sub in s200.get_subnets()]

    diffs = compare_lists(legacy_subs, s200_subs)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique subnets found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique subnets found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs['unique_to_s200'] and not diffs['unique_to_legacy']:
        logger.write_log("Subnet names match for both legacy and s200.", show_output=True)

# Check object store accounts
def check_object_store_accounts():
    logger.write_log("Check if object store accounts match between FBs.", show_output=True)

    legacy_obj_accounts = [acct["name"] for acct in legacy.get_object_store_accounts()]
    s200_obj_accounts = [acct["name"] for acct in s200.get_object_store_accounts()]

    diffs = compare_lists(legacy_obj_accounts, s200_obj_accounts)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique object store accounts found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique object store accounts found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs['unique_to_s200'] and not diffs['unique_to_legacy']:
        logger.write_log("Object store account names match for both legacy and s200.", show_output=True)

# Check object store users
def check_object_store_users():
    logger.write_log("Check if object store users match between FBs.", show_output=True)

    legacy_obj_users = [user["name"] for user in legacy.get_object_store_users()]
    s200_obj_users = [user["name"] for user in s200.get_object_store_users()]

    diffs = compare_lists(legacy_obj_users, s200_obj_users)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique object store users found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique object store users found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs['unique_to_s200'] and not diffs['unique_to_legacy']:
        logger.write_log("Object store users match for both legacy and s200.", show_output=True)

# Check object store buckets
def check_buckets():
    logger.write_log("Check if buckets match between FBs.", show_output=True)

    legacy_buckets = [buck["name"] for buck in legacy.get_buckets()]
    s200_buckets = [buck["name"] for buck in s200.get_buckets()]

    diffs = compare_lists(legacy_buckets, s200_buckets)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique bucket names found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique bucket names found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs['unique_to_s200'] and not diffs['unique_to_legacy']:
        logger.write_log("Bucket names match for both legacy and s200.", show_output=True)

# Check Directory Services point to valid LDAPS server on S200
def check_directory_services(show_only_diffs=True):
    logger.write_log("Check if directory services configured are valid for s200.")

    legacy_ds = next((ds for ds in legacy.get_directory_services() if "management" in ds["services"]), None)
    s200_ds = next((ds for ds in s200.get_directory_services() if "management" in ds["services"]), None)

    final_dict = {
        "legacy_directory_services": {
            "enabled": legacy_ds["enabled"],
            "base_dn": legacy_ds["base_dn"],
            "bind_user": legacy_ds["bind_user"],
            "uris": legacy_ds["uris"]
        },
        "s200_directory_services": {
            "enabled": s200_ds["enabled"],
            "base_dn": s200_ds["base_dn"],
            "bind_user": s200_ds["bind_user"],
            "uris": s200_ds["uris"]
        }
    }
    if show_only_diffs:
        keys_to_delete = [key for key, val in final_dict["legacy_directory_services"].items() if val == final_dict["s200_directory_services"][key]]
    else:
        keys_to_delete = None

    if keys_to_delete:
        for key in keys_to_delete:
            del final_dict["legacy_directory_services"][key]
            del final_dict["s200_directory_services"][key]

    if final_dict["legacy_directory_services"] or final_dict["s200_directory_services"]:
        logger.write_log("Some directory service items don't match between FBs.", jsondata=final_dict, show_output=True)
    else:
        logger.write_log("Directory services match for both legacy and s200.", show_output=True)


# Check DNS settings point to valid DNS server on S200
def check_dns(show_only_diffs=True):
    logger.write_log("Check if DNS configurations are valid for s200.")

    legacy_dns = legacy.get_dns()[0]
    s200_dns = s200.get_dns()[0]

    final_dict = {
        "legacy_dns": {
            "domain": legacy_dns["domain"],
            "nameservers": legacy_dns["nameservers"]
        },
        "s200_dns": {
            "domain": s200_dns["domain"],
            "nameservers": s200_dns["nameservers"]
        }
    }
    if show_only_diffs:
        keys_to_delete = [key for key, val in final_dict["legacy_dns"].items() if val == final_dict["s200_dns"][key]]
    else:
        keys_to_delete = None

    if keys_to_delete:
        for key in keys_to_delete:
            del final_dict["legacy_dns"][key]
            del final_dict["s200_dns"][key]

    if final_dict["legacy_dns"] or final_dict["s200_dns"]:
        logger.write_log("Some DNS configurations don't match between FBs.", jsondata=final_dict, show_output=True)
    else:
        logger.write_log("DNS configurations match for both legacy and s200.", show_output=True)

# Check NTP settings point to valid NTP server on S200
def check_arrays(show_only_diffs=True):
    logger.write_log("Check if array configurations are valid for s200.")

    legacy_array = legacy.get_array_configurations()[0]
    s200_array = s200.get_array_configurations()[0]

    final_dict = {
        legacy_array["name"]: {
            "banner": legacy_array["banner"],
            "idle_timeout": legacy_array["idle_timeout"],
            "ntp_servers": legacy_array["ntp_servers"],
            "time_zone": legacy_array["time_zone"],
            "encryption_at_rest": legacy_array["encryption"]["data_at_rest"]["enabled"]
        },
        s200_array["name"]: {
            "banner": s200_array["banner"],
            "idle_timeout": s200_array["idle_timeout"],
            "ntp_servers": s200_array["ntp_servers"],
            "time_zone": s200_array["time_zone"],
            "encryption_at_rest": s200_array["encryption"]["data_at_rest"]["enabled"]
        }
    }
    if show_only_diffs:
        keys_to_delete = [key for key, val in final_dict[legacy_array["name"]].items() if val == final_dict[s200_array["name"]][key]]
    else:
        keys_to_delete = None

    if keys_to_delete:
        for key in keys_to_delete:
            del final_dict[legacy_array["name"]][key]
            del final_dict[s200_array["name"]][key]

    if final_dict[legacy_array["name"]] or final_dict[s200_array["name"]]:
        logger.write_log("Some array configurations don't match between FBs.", jsondata=final_dict, show_output=True)
    else:
        logger.write_log("Array configurations match for both legacy and s200.", show_output=True)

# Check file systems match, if not show differences
def check_file_system_sizes():
    def h_readable_size(bytes):
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(bytes)
        for unit in units:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"
    
    logger.write_log("Checking if file system names match between FBs.", show_output=True)

    legacy_filesystems = legacy.get_filesystems()
    s200_filesystems = s200.get_filesystems()
    
    size_data = []

    for lfs in legacy_filesystems:
        for sfs in s200_filesystems:
            if lfs["name"] == sfs["name"]:
                lfs_size = lfs["space"]["virtual"]
                sfs_size = sfs["space"]["virtual"]
                dif_size = abs(lfs_size - sfs_size)
                data = {
                    "filesystem": lfs["name"],
                    "size_on_legacy": h_readable_size(lfs_size),
                    "size_on_s200": h_readable_size(sfs_size),
                    "size_diff": h_readable_size(dif_size)
                }
                size_data.append(data)
                break
    logger.write_log(f"File System Size Differences.", jsondata=size_data, show_output=True)


if __name__ == "__main__":
    check_file_systems()
    check_snapshot_policies()
    check_matching_attached_snapshot_policies()
    check_subnets()
    check_object_store_accounts()
    check_object_store_users()
    check_buckets()
    check_directory_services()
    check_dns()
    check_arrays()
    check_file_system_sizes()