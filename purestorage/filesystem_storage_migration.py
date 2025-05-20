#!/usr/bin/bash
import pure_migration_v3 as pv3

### Filesystem migration ###

def Migrate_Filesystems():
    # Get auth token
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    # Get filesystem list
    filesystems = pv3.Get_Filesystems(pv3.API_TOKEN, pv3.PB1_MGT)

    # Let the loop begin to POST
    for fs in filesystems:
        # Get S200 auth token
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
        jan_01_2024 = 1704067200000
        if fs["created"] > jan_01_2024:
            # TODO
            print(f"Skipping {fs}, replication handling logic coming soon")
            # API 4 posts to start replication
            # connection key -> array connection -> target -> replica link
            continue

        # FS check is None so develop payload and POST the filesystm
        post_check = pv3.Post_Filesystem(auth_token_s200, pv3.PB2_MGT, fs_name, fs)
        
        if post_check == 200:
            

    print("Filesystems done.")
    print()


### Script ###
if __name__ == "__main__":
    Migrate_Filesystems()