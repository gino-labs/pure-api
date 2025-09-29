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

# Check file systems match, if not show differences
def check_file_systems():
    legacy_filesystems = [fs["name"] for fs in legacy.get_filesystems()]
    s200_filesystems = [fs["name"] for fs in s200.get_filesystems()]

    s200_diffs = set(s200_filesystems) - set(legacy_filesystems)
    legacy_diffs = set(legacy_diffs) - set(s200_diffs)

    if s200_diffs:
        logger.write_log("Different file systems found on s200 with following names: ", jsondata=s200_diffs, show_output=True)
    if legacy_diffs:
        logger.write_log("Different file systems found legacy with following names: ", jsondata=legacy_diffs, show_output=True)
    if not s200_diffs and not legacy_diffs:
        logger.write_log("File system names match for both legacy and s200.")


# Check if replica links are present for each file system on Legacy
def check_replica_links_filesystems():
    legacy_filesystems = legacy.get_filesystems()
    legacy_replica_links = legacy.get_filesytem_replica_links()

    legacy_replica_fs_list = [link["local_file_system"]["name"] for link in legacy_replica_links]

    non_replica_fs_list = []
    for fs in legacy_filesystems:
        if fs["name"] not in legacy_replica_fs_list:
            temp_dict = {
                "name": fs["name"],
                "space": fs["space"]["total_physical"],
                "writable": fs["writable"]
            }
            non_replica_fs_list.append(temp_dict)

    logger.write_log("Filesystems with no replication links", jsondata=non_replica_fs_list, show_output=True)

# Check for non replication snapshot policies from legacy on s200 
def check_snapshot_policies():
    legacy_policies = set([pol["name"] for pol in legacy.get_snapshot_policies() if "5_min" not in pol["name"]])
    s200_policies = set([pol["name"] for pol in s200.get_snapshot_policies() if "5_min" not in pol["name"]])

    if legacy_policies.issubset(s200_policies):
        logger.write_log("All snapshot polices from legacy are present on s200", jsondata=list(legacy_policies), show_output=True)
    else:
        diff_policies = legacy_policies - s200_policies
        logger.write_log("Polices on Legacy not found on S200", jsondata=list(diff_policies), show_output=True)

# Check that file systems on both legacy and s200 have same snapshot polices
def check_matching_attached_snapshot_policies():
    legacy_fs_attch_pols = legacy.get_filesystems_attached_to_snapshot_policy()
    s200_fs_attch_pols = s200.get_filesystems_attached_to_snapshot_policy()

    legacy_policy_and_members = {}
    for fs_pol in legacy_fs_attch_pols:
        if fs_pol["policy"]["name"] not in legacy_policy_and_members:
            legacy_policy_and_members[fs_pol["policy"]["name"]] = []
        legacy_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for Legacy...", jsondata=legacy_policy_and_members, show_output=True)

    s200_policy_and_members = {}
    for fs_pol in s200_fs_attch_pols:
        if fs_pol["policy"]["name"] not in s200_policy_and_members:
            s200_policy_and_members[fs_pol["policy"]["name"]] = []
        s200_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for S200...", jsondata=s200_policy_and_members, show_output=True)

    for pol, member_list in legacy_policy_and_members.items():
        if pol not in s200_policy_and_members:
            continue
        legacy_members = set(member_list)
        s200_members = set(s200_policy_and_members[pol])

        if legacy_members.issubset(s200_members):
            logger.write_log(f"Attached snapshot policy \"{pol}\" has MATCHING filesystem members on both FlashBlades", jsondata=member_list, show_output=True)
        else:
            diff_members = legacy_members - s200_members
            logger.write_log(f"Attached snapshot policy \"{pol}\" has MISSING filesystem members on s200.", jsondata=list(diff_members), show_output=True)

# Check subnets names and vlans match for data interfaces

# Verify network interfaces (data matches, mgmt present)

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