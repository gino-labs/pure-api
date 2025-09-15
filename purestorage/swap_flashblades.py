#!/usr/bin/env python3
import purefb_api as pfa
import purefb_log as pfl

# Logger object
purelog = pfl.PureLog()

# FlashBlade API Object Instances
Legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

# Get Legacy file systems

# Get S200 file systems

# Get Legacy interfaces' info

# Store Production IPs in variable to pass to ansible playbook later

# Get S200 interfaces' info

# Get file system replica links on Legacy

# Get active NFS clients before swapping

# Create inventory file with NFS clients obtained

# Create final snapshots on Legacy and wait 30 seconds for them to settle

# Demote / Disable each file system on Legacy (Handle exception: non-replication snapshot error, skip demotion)

# Patch Legacy IPs to S200

# Patch S200 IPs to Legacy

# Delete replica links on Legacy

# Promote / Enabled each file system on S200

# Run ansible playbook with nfs client inventory and production IP variable

# Clean up
