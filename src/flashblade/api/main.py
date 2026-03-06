#!/usr/bin/env python3
from flashblade.api.core import ApiSession, ApiError
from flashblade.api.resources import *

class ApiError(Exception):
    def __init__(self, message: str, code: int, context: str):
        self.code = code
        self.context = context
        self.message = message
        super().__init__(f"API Error:\n\tCode: {code} \n\tContext: {context} \n\t{message}")

class FlashBladeAPI(FBGet, FBPatch, FBPost, FBDelete):
    def __init__(self, name: str, mgt_ip: str, api_token: str, data_ip=None):
        super().__init__(session=ApiSession(mgt_ip, api_token))
        self.name = name
        self.data_ip = data_ip
