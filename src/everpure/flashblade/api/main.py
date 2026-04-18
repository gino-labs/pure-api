from everpure.flashblade.api.resources import *

class FlashBladeAPI(FBGet, FBPatch, FBPost, FBDelete):
    def __init__(self, mgt_ip: str, api_token: str, data_ip=None):
        super().__init__(session=ApiSession(mgt_ip, api_token))
        self.array = self.get_arrays()[0]
        self.name = self.array["name"]
        self.data_ip = data_ip
