#!/usr/bin/env python3
import pure_migration_v3 as pv3
import time

# Do Incremental Rsync on non-replication filesystems
def Rsync_Incremental_Migration():
    # Get auth token
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)

    # Get filesystem list
    filesystems = pv3.Get_Filesystems(auth_token, pv3.PB1_MGT)

    # Let the loop begin to POST
    for fs in filesystems:
        # Get S200 auth token
        auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)

        # Check if fs exists already
        fs_name = fs["name"]
        fs_check = pv3.Get_Single_Filesystem(fs_name, auth_token_s200, pv3.PB2_MGT)

        # Skip Anaconda
        if fs_name == "anaconda_linux_tucson":
            print(f"Skipping {fs_name}\nAnaconda has been discontinued...")
            print()
            time.sleep(5)
            continue

        # Check if fs_check recieved an existing item
        if fs_check is not None:
            print(f"Filesystem already exists: {fs_check['name']}")
            print()
        else:
            # Post the filesystem
            post_check = pv3.Post_Filesystem(auth_token_s200, pv3.PB2_MGT, fs_name, fs)

        # Check cutoff date and skip replication filesystems
        cutoff_date = int(pv3.REPLICATION_CUTOFF)
        if fs["created"] > cutoff_date:
            # TODO
            print(f"Skipping rsync for {fs_name}, handled by replication")
            print()
            # API 4 posts to start replication, considering separate script
            # connection key -> array connection -> target -> replica link
            time.sleep(5)
            continue

        rsync_list = []
        # Mount and Migrate with RSYNC
        try:
            # Begin pcopy and rsync prep
            pv3.Patch_Export_Rule(fs_name, auth_token, pv3.PB1_MGT)
            
            # Mkdir
            pv3.Mkdir2(fs_name)

            # Mount
            pv3.Mount2(fs_name)

            # Rsync
            pv3.Rsync(fs_name, verbose=True, sparse=True)

            # Umount
            pv3.Unmount2(fs_name)

            # Append to list if completed
            rsync_list.append(fs_name) 
        except Exception as e:
            print(f"Exception occured, skipping {fs_name}\n{e}")
            print()
            continue
        print("----------------")
        print()
        time.sleep(2)


    print("Filesystems Rsynced")
    for item in rsync_list:
        print(f"- {item}")
    print()

if __name__ == "__main__":
    Rsync_Incremental_Migration()
