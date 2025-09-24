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

def check_replica_links_filesystems():
    legacy_filesystems = legacy.get_filesystems()
    legacy_replica_links = legacy.get_filesytem_replica_links()

    legacy_fs_list = [fs["name"] for fs in legacy_filesystems]
    legacy_replica_fs_list = [link["local_file_system"]["name"] for link in legacy_replica_links]

    non_replica_fs_list = list(set(legacy_fs_list) - set(legacy_replica_fs_list))

    logger.write_log("FlashBlade migration check: File systems present on Legacy FB with no replication link", jsondata=non_replica_fs_list, show_output=True)
    logger.write_log("FlashBlade file systems will not be able to be demoted if snapshot is taken and is non-replication", show_output=True)

    test_fs = s200.get_filesystems(filesystems="test", dumpjson=True)

if __name__ == "__main__":
    check_replica_links_filesystems()