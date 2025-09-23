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