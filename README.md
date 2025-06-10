# gxc-purestorage scripts

## Pure Storage

Alright so these are some scripts to help out with pure storage migrations to the new s200 appliances. It ain't the prettiest code, but it's been helping me get the job done vs. tedious data entry. Alot of the code I edited, changed, and commented on the fly while using them for migration. Double check __name__ == "__main__" at the bottom of the scripts.

Empahsized data protection of the source blade to be `read-only` whenever possible.

I'm not gonna lie if you're reading this and you're trying to use the scripts, good luck! Best practices and reusability fell short due to time and development. 

### Step 1
- Generate API tokens for `pureuser` on old and new pure appliances
- We're going to use these to make our API requests.

### Step 2
- Copy `purestorage/pure_env_template.sh` to a file like `my_site_env.sh` (You can name it whatever you just need to source it for environment variables.)
- Fill out `my_site_env.sh` with the appropratiate information.
    - Note: PB1 prefixs are source flashblade, PB2 prefixes are destination flashblade.
- Once filled out run the following commands:
```bash
source my_site_env.sh
printenv | grep -i api
```
- If successful you should see both API TOKENs for each flashblade.

### Step 3
- With your environment variables set you can run the following scripts for migration.
- Filesystems pcopy/rsync: `purestorage/filesystem_storage_migration.py`
- Object Storage and Components: `purestorage/object_storage_migration.py`
- Subnets and Interfaces: `purestorage/subs_ints_migration.py`
- Rsync only filesystems: `purestorage/rsync_incremental_migration.py` 

#### Currently in progress
- File Replication: `purestorage/filesystem_replication_migration.py`

