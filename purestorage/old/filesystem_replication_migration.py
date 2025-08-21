#!/usr/bin/env python3
import pure_migration_v3 as pv3

# Migration of filesystems via replication as applicable

def Replicate_Filesystems():
    # Tokens
    auth_token = pv3.Get_Session_Token(pv3.API_TOKEN, pv3.PB1_MGT)
    auth_token_s200 = pv3.Get_Session_Token(pv3.API_TOKEN_S200, pv3.PB2_MGT)    

    # Set up connection keys

    # Set up array connections

    # Set up replication target to new array

    # Set up replica links of appropriate filesystems

    