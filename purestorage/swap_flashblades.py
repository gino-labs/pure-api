#!/usr/bin/env python3
import purefb_api as pfa
import purefb_log as pfl
import subprocess
import tempfile
import time
import json
import os

# Logger object
scriptlog = pfl.PureLog()

# FlashBlade API Object Instances
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

# Get Legacy file systems
legacy.get_filesystems()

# Get S200 file systems
s200.get_filesystems()

# Get Legacy interfaces' info
legacy.get_interfaces()

# Store Production IPs in variable to pass to ansible playbook later

# Get S200 interfaces' info
s200.get_interfaces()

# Get file system replica links on Legacy
legacy.get_filesytem_replica_links()

# Get active NFS clients before swapping
legacy.get_nfs_clients()

# Create inventory file with NFS clients obtained

# Create final snapshots on Legacy and wait 30 seconds for them to settle

# Demote / Disable each file system on Legacy (Handle exception: non-replication snapshot error, skip demotion)

# Patch Legacy IPs to S200

# Patch S200 IPs to Legacy

# Delete replica links on Legacy

# Promote / Enabled each file system on S200

# Run ansible playbook with nfs client inventory and production IP variable

# Clean up
