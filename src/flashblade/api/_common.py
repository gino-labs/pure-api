import requests

class ApiError(Exception):
    def __init__(self, message: str, code: int, context: str):
        self.code = code
        self.context = context
        self.message = message
        super().__init__(f"API Error:\n\tCode: {code} \n\tContext: {context} \n\t{message}")

class ApiSession(requests.Session):
    def __init__(self, mgt_ip: str, api_token: str):
        super().__init__()
        self.mgt_ip = mgt_ip
        self.baseurl = f"https//{mgt_ip}/api/2.latest"
        self.api_token = api_token
        self.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": self.auth_token()
        })

    def auth_token(self):
        headers = {"api-token": self.api_token}
        login_url = f"https://{self.mgt_ip}/api/login"
        login_response = requests.post(login_url, headers=headers, verify=False)
        login_response.raise_for_status()
        return login_response.headers.get("x-auth-token")