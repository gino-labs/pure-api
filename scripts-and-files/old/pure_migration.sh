#!/usr/bin/env bash


## Variables Needed to use script
PB1='pb1' # Hostname / IP
PB2='pb2' # Hostname / IP


# Check Filesystem name passed can be seen from showmount of pb1 and pb2 

if [ -z "$1" ]; then
    echo "Error: Provide filesystem name!"
    exit 1
fi

# Assign filesystem var after verfiying not empty
FS="$1"


if [ "$FS" == "$(showmount -e "$PB1" | grep -o "$FS")" ]; then
    echo "Valid filesystem, continuing..."
    sleep 1
else
    echo "Invalid filesystem: $FS"
    sleep 3
    exit 1
fi

# On local box create directories and mount for migration
mkdir -p /mnt/pure_migration/"$FS"_source
mount -t nfs -o ro "$PB1":/"$FS" /mnt/pure_migration/"$FS"_source
mkdir -p /mnt/pure_migration/"$FS"_migration
mount -t nfs -o rw "$PB2":/"$FS" /mnt/pure_migration/"$FS"_migration


# Run pcopy from source to destination
echo -e "Mounted, beginning pcopy...\n"
pcopy -pr /mnt/pure_migration/"$FS"_source/. /mnt/pure_migration/"$FS"_migration/


# Run rsync for good measure, ignoring .snapshot
echo -e "Finished pcopy, starting rsync for good measure"
rsync -havH --progress --exclude '.snapshot/' /mnt/pure_migration/"$FS"_source/ /mnt/pure_migration/"$FS"_migration/


# Check byte difference between both directories
USED1=$(df --block-size=1 /mnt/pure_migration/"$FS"_source | awk 'NR==2 {print $2}')
USED2=$(df --block-size=1 /mnt/pure_migration/"$FS"_migration | awk 'NR==2 {print $2}')
DIFF_BYTES=$((USED1 - USED2))

echo -e "\n---\nCopying done."
echo -e "Byte difference between $PB1 and $PB2 is: $DIFF_BYTES"
sleep 3


# Prompt user to continue to unmount or leave mounted for manual checking
echo -e "\nWould you like to unmount NFS shares? y/n"
read -r answer

if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo "Continuing to umount..."
    sleep 3
elif [[ "$answer" =~ ^[Nn]$ ]]; then
    echo "Exiting..."
    sleep 2
    exit 0
fi

# umount nfs mounts if done with them
umount /mnt/pure_migration/"$FS"_source/
umount /mnt/pure_migration/"$FS"_migration/
rmdir /mnt/pure_migration/"$FS"_source/
rmdir /mnt/pure_migration/"$FS"_migration/


