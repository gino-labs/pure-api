#!/usr/bin/bash
import pure_migration_v3 as pv3

### Filesystem migration ###

def Migrate_Filesystems():
    # Get auth token
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    # Get filesystem list
    filesystems = pv3.Get_Filesystems(auth_token, pv3.PB1_MGT)

    # Let the loop begin to POST
    for fs in filesystems:
        # Get auth tokens
        auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        # Check if fs exists already
        fs_name = fs["name"]
        fs_check = pv3.Get_Single_Filesystem(fs_name, auth_token_s200, pv3.PB2_MGT)

        # Check if fs_check recieved an existing item
        if fs_check is not None:
            print(f"Filesystem already exists: {fs_check['name']}")
            print()
            continue

        # Check date, if 2024 and up create a replica link for replication
        cutoff_date = pv3.REPLICATION_CUTOFF
        if fs["created"] > cutoff_date:
            # TODO
            print(f"Skipping {fs_name}, replication handling logic coming soon")
            # API 4 posts to start replication, considering separate script
            # connection key -> array connection -> target -> replica link
            continue
        
        # FS check is None so develop payload and POST the filesystm
        del fs["promotion_status"]
        del fs["created"]
        del fs["source"]
        del fs["id"]
        del fs["space"]
        del fs["time_remaining"]
        del fs["destroyed"]
        del fs["name"]
        del fs["requested_promotion_state"]
        del fs["smb"]

        post_check = pv3.Post_Filesystem(auth_token_s200, pv3.PB2_MGT, fs_name, fs)
        
        if post_check == 200:
            try:
                # Begin pcopy and rsync prep
                pv3.Patch_Export_Rule(fs_name, auth_token, pv3.PB1_MGT)
                
                # Mkdir
                pv3.Mkdir2(fs_name)

                # Mount
                pv3.Mount2(fs_name)

                # Pcopy
                pv3.Pcopy(fs_name, sparse=True)

                # Rsync
                pv3.Rsync(fs_name, sparse=True)

                # Umount
                pv3.Unmount2(fs_name)
            except Exception as e:
                print(f"Exception occured, skipping {fs_name}\n{e}")
                print()
                continue

    print("Filesystems done.")
    print()


### Script ###
if __name__ == "__main__":
    Migrate_Filesystems()