import requests

class ApiError(Exception):
    def __init__(self, message: str, code: int, context: str):
        self.code = code
        self.context = context
        self.message = message
        super().__init__(f"API Error:\n\tCode: {code} \n\tContext: {context} \n\t{message}")

class ApiSession(requests.Session):
    def __init__(self, mgt: str, token: str):
        super().__init__()
        self.mgt = mgt
        self.token = token
        self.baseurl = f"https://{mgt}/api/2.latest"
        self.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": self.auth_token()
        })

    def auth_token(self):
        headers = {"api-token": self.token}
        login_url = f"https://{self.mgt}/api/login"
        login_response = requests.post(login_url, headers=headers, verify=False)
        login_response.raise_for_status()
        return login_response.headers.get("x-auth-token")