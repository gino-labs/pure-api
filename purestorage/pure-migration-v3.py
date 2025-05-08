#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib3
import requests
import argparse
import subprocess
from datetime import datetime

# Disabling Insecure Requests Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

################# GLOBAL VARIABLES #################
PB1 = ""                                           #
PB2 = ""                                           #
PB1_MGT = ""                                       #
PB2_MGT = ""                                       #
LOCAL_IP = ""                                      #
API_TOKEN = os.getenv("API_TOKEN")                 #
API_TOKEN_S200 = os.getenv("API_TOKEN_S200")       #
MIGRATION_POLICY = ""                              #
####################################################