#!/usr/bin/env python3
from flashblade.api.core import ApiSession
from flashblade.api.resources import *

class FlashBladeAPI(FBGet, FBPatch, FBPost, FBDelete):
    def __init__(self, name: str, mgt_ip: str, api_token: str, data_ip=None):
        super().__init__(session=ApiSession(mgt_ip, api_token))
        self.name = name
        self.data_ip = data_ip
