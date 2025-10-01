from purefb_log import *
from purefb_api import *

'''
What to check?
- Matching File System names
- Matching data interface names
- Replication links
- File systems without repliaction links won't be demotable if snapshot is taken.
'''

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

# Check if replica links are present for each file system on Legacy
def check_replica_links_filesystems(show_fs_data=False):
    logger.write_log("Check if legacy file systems have replication links.", show_output=True)

    legacy_filesystems = legacy.get_filesystems()
    legacy_replica_links = legacy.get_filesytem_replica_links()
    
    legacy_fs_list = [fs["name"] for fs in legacy_filesystems]
    legacy_replica_fs_list = [link["local_file_system"]["name"] for link in legacy_replica_links]

    non_replica_fs_list = compare_lists(legacy_fs_list, legacy_replica_fs_list, check_one=True)

    logger.write_log(f"Legacy Filesystems with no replication links: {len(non_replica_fs_list)}", jsondata=non_replica_fs_list, show_output=True)

    if show_fs_data:
        fs_data = []
        filesystems = legacy.get_filesystems(filesystems=non_replica_fs_list)
        for fs in filesystems:
            temp_dict = {
                "name": fs["name"],
                "space": fs["space"]["total_physical"],
                "writable": fs["writable"]
            }
            fs_data.append(temp_dict)
        logger.write_log("Logging additional data for non replication file systems.", jsondata=fs_data)

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

    legacy_fs_attch_pols = legacy.get_filesystems_attached_to_snapshot_policy()
    s200_fs_attch_pols = s200.get_filesystems_attached_to_snapshot_policy()

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

# Verify network interfaces (data matches, mgmt present)
def check_interfaces():
    logger.write_log("Check if network interfaces match between FBs. NOTE: Can't create matching interface without different IP address.", show_output=True)

    legacy_ifaces = [iface["name"] for iface in legacy.get_interfaces()]
    s200_ifaces = [iface["name"] for iface in s200.get_interfaces()]

    diffs = compare_lists(legacy_ifaces, s200_ifaces)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Unique network interfaces found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Unique network interfacess found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs['unique_to_s200'] and not diffs['unique_to_legacy']:
        logger.write_log("Subnet names match for both legacy and s200.", show_output=True)


# Check NFS Rules match Legacy
def check_filesystem_nfs_rules():
    logger.write_log("Check if NFS rules match per file system between FBs.", show_output=True)

    legacy_filesystem_names_rules = {{fs["name"]: fs["nfs"]["rules"]} for fs in legacy.get_filesystems()}
    s200_filesystems = s200.get_filesystems()

    non_matches = {}
    for fs in s200_filesystems:
        if fs["name"] in legacy_filesystem_names_rules:
            if fs["nfs"]["rules"] not in legacy_filesystem_names_rules[fs["name"]]:
                temp_dict = {
                        "s200_rules": fs["nfs"]["rules"],
                        "legacy_rules": legacy_filesystem_names_rules[fs["name"]]
                    }
                non_matches[fs["name"]] = temp_dict

    logger.write_log("File systems that didn't have matching NFS rules between FBs.", jsondata=non_matches, show_output=True)


# Check object storage components match (Accounts, Buckets, Users)

# Check if object replication in place per bucket

# Check Directory Services point to valid LDAPS server on S200

# Check DNS settings point to valid DNS server on S200

# Check NTP settings point to valid NTP server on S200

# Check certificates/groups are valid on S200

if __name__ == "__main__":
    check_replica_links_filesystems()
    check_snapshot_policies()
    check_matching_attached_snapshot_policies()
    check_file_systems()
    check_subnets()
    check_filesystem_nfs_rules()