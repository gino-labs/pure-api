#!/usr/bin/env python3
import os
import time
import json
import urllib3
import requests
from datetime import datetime

# Disabling Insecure Requests Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

################### ENVIRONMENT VARIABLES ###################  
PB1 = os.getenv("PB1")                                      #
PB2 = os.getenv("PB2")                                      #
PB1_MGT = os.getenv("PB1_MGT")                              #
PB2_MGT = os.getenv("PB2_MGT")                              #
LOCAL_IP = os.getenv("LOCAL_IP")                            #
API_TOKEN = os.getenv("API_TOKEN")                          #
API_TOKEN_S200 = os.getenv("API_TOKEN_S200")                #
MIGRATION_POLICY = os.getenv("MIGRATION_POLICY")            #
REPLICATION_CUTOFF = os.getenv("REPLICATION_CUTOFF")        #
#############################################################