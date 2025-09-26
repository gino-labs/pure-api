import purefb_log
import purefb_api

'''
What to check?
- Matching File System names
- Matching data interface names
- Replication links
- File systems without repliaction links won't be demotable if snapshot is taken.
- Usable error code/message for exception handling?
{"errors":[{"code":32,"context":"tools_linux_chantilly","message":"The latest snapshot tools_linux_chantilly.2025_09_12_15_09 is not a replication snapshot.
 To demote a file system it must either have no snapshots or the most recent snapshot must be a replication snapshot."}]}
'''

logger = purefb_log.PureLog()

legacy = purefb_api.FlashBladeAPI(purefb_api.PB1, purefb_api.PB1_MGT, purefb_api.API_TOKEN)
s200 = purefb_api.FlashBladeAPI(purefb_api.PB2, purefb_api.PB2_MGT, purefb_api.API_TOKEN_S200)

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
    legacy_fs_attch_pols = legacy.get_filesystems_attached_to_snapshot_policy(dumpjson=True)
    s200_fs_attch_pols = s200.get_filesystems_attached_to_snapshot_policy(dumpjson=True)

    legacy_policy_and_members = {}
    for fs_pol in legacy_fs_attch_pols:
        if fs_pol["policy"]["name"] not in legacy_policy_and_members:
            legacy_policy_and_members[fs_pol["policy"]["name"]] = []
        legacy_policy_and_members[fs_pol["policy"]["name"]].append(fs_pol["member"]["name"])

    logger.write_log("Policies and members for Legacy...", jsondata=legacy_policy_and_members, show_output=True)

    s200_policy_and_members = {}
    for fs_pol in legacy_fs_attch_pols:
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
            logger.write_log(f"Attached snapshot policy \"{pol}\" has matching filesystem members on both FlashBlades", jsondata=member_list, show_output=True)
        else:
            diff_members = legacy_members - s200_members
            logger.write_log(f"Attached snapshot policy \"{pol}\" has missing filesystem members on s200.", jsondata=list(diff_members), show_output=True)


if __name__ == "__main__":
    check_replica_links_filesystems()
    check_snapshot_policies()
    check_matching_attached_snapshot_policies()