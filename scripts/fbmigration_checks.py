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
    legacy_filesystems = [fs["name"] for fs in legacy.get_filesystems()]
    s200_filesystems = [fs["name"] for fs in s200.get_filesystems()]

    diffs = compare_lists(legacy_filesystems, s200_filesystems)

    if diffs["unique_to_legacy"]:
        logger.write_log(f"Different file systems found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Different file systems found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs["unique_to_s200"] and not diffs["unique_to_legacy"]:
        logger.write_log("File system names match for both legacy and s200.")

# Check if replica links are present for each file system on Legacy
def check_replica_links_filesystems(show_fs_data=False):
    legacy_filesystems = legacy.get_filesystems()
    legacy_replica_links = legacy.get_filesytem_replica_links()
    
    legacy_fs_list = [fs["name"] for fs in legacy_filesystems]
    legacy_replica_fs_list = [link["local_file_system"]["name"] for link in legacy_replica_links]

    non_replica_fs_list = compare_lists(legacy_fs_list, legacy_replica_fs_list, check_one=True)

    logger.write_log("Filesystems with no replication links", jsondata=non_replica_fs_list, show_output=True)

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
    legacy_policies = set([pol["name"] for pol in legacy.get_snapshot_policies() if "5_min" not in pol["name"]])
    s200_policies = set([pol["name"] for pol in s200.get_snapshot_policies() if "5_min" not in pol["name"]])

    diffs = compare_lists(legacy_policies, s200_policies)
    if diffs["unique_to_legacy"]:
        logger.write_log(f"Different snapshot policy names found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if diffs["unique_to_s200"]:
        logger.write_log(f"Different snapshot policy names found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if not diffs["unique_to_s200"] and not diffs["unique_to_legacy"]:
        logger.write_log("Snapshot policy names match for both legacy and s200.")

# Check that file systems on both legacy and s200 have same snapshot polices
def check_matching_attached_snapshot_policies():
    legacy_fs_attch_pols = legacy.get_filesystems_attached_to_snapshot_policy()
    s200_fs_attch_pols = s200.get_filesystems_attached_to_snapshot_policy()

    # Build out dictionary containing legacy policies and associated file system members
    legacy_policy_and_members = {}
    for fs_pol in legacy_fs_attch_pols:
        if fs_pol["policy"]["name"] not in legacy_policy_and_members:
            legacy_policy_and_members[fs_pol["policy"]["name"]] = []
        legacy_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for Legacy...", jsondata=legacy_policy_and_members, show_output=True)

    # Build out dictionary containing s200 policies and associated file system members
    s200_policy_and_members = {}
    for fs_pol in s200_fs_attch_pols:
        if fs_pol["policy"]["name"] not in s200_policy_and_members:
            s200_policy_and_members[fs_pol["policy"]["name"]] = []
        s200_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for S200...", jsondata=s200_policy_and_members, show_output=True)

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
            logger.write_log(f"Attached snapshot policy \"{pol}\" has MATCHING filesystem members on both FlashBlades", jsondata=member_list, show_output=True)

# Check subnets names and vlans match for data interfaces
def check_subnets():
    legacy_subs = [sub["name"] for sub in legacy.get_subnets()]
    s200_subs = [sub["name"] for sub in s200.get_subnets()]

    diffs = compare_lists(legacy_subs, s200_subs)

    if diffs["unique_to_s200"]:
        logger.write_log(f"Different subnets found on s200: {len(diffs['unique_to_s200'])}", jsondata=list(diffs["unique_to_s200"]), show_output=True)
    if diffs["unique_to_legacy"]:
        logger.write_log(f"Different subnets found on legacy: {len(diffs['unique_to_legacy'])}", jsondata=list(diffs["unique_to_legacy"]), show_output=True)
    if not diffs['unique_to_s200'] and not diffs['unique_to_legacy']:
        logger.write_log("Subnet names match for both legacy and s200.")

# Verify network interfaces (data matches, mgmt present)
def check_interfaces():
    legacy_ifaces = [iface["name"] for iface in legacy.get_interfaces()]
    s200_ifaces = [iface["name"] for iface in s200.get_interfaces()]


# Check NFS Rules match Legacy

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