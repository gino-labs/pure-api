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

class FlashBladeAPI():
    def __init__(self, data_ip, mgt_ip, api_token):
        self.data_ip = data_ip
        self.mgt_ip = mgt_ip
        self.api_token = api_token
        self.baseurl = f"https://{mgt_ip}/api/2.latest/"
        self.auth_token = self.Get_Session_Token()
        self.auth_headers = self.Set_Auth_Headers()

    def Get_Session_Token(self):
        url = f"https://{self.mgt_ip}/api/login"

        headers = {
        "api-token": self.api_token,
        "Content-Type": "application/json"
    }
        response = requests.post(url, headers=headers, verify=False)

        if response.status_code == 200:
            return response.headers.get("x-auth-token")
        else:
            print(f"Login failed. Status Code: {response.status_code}\n{response.text}")
            print()
            return None
        
    def Set_Auth_Headers(self):
        headers = {
            "x-auth-token": self.auth_token,
            "Content-Type": "application/json"
        }
        return headers