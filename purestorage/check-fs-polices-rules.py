#!/usr/bin/env python3
import purefb_api as pfa
import json

# Initialize api sessions to each blade
legacy = pfa.FlashBladeAPI(pfa.PB1, pfa.PB1_MGT, pfa.API_TOKEN)
s200 = pfa.FlashBladeAPI(pfa.PB2, pfa.PB2_MGT, pfa.API_TOKEN_S200)

s200_filesystems = s200.get_filesystems()

for fs in s200_filesystems:
    print(json.dumps(fs["nfs"], indent=4))
    print()