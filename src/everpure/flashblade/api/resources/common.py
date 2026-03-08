import requests

class ApiError(Exception):
    def __init__(self, response: requests.Response):
        json = response.json()
        if "errors" in json:
            self.err_code = json["errors"][0]["code"]
            self.err_context = json["errors"][0]["context"]
            self.err_message = json["errors"][0]["message"]
            super().__init__(f"API Error:\n\tCode: {self.err_code} \n\tContext: {self.err_context} \n\t{self.err_message}")
        else:
            super().__init__()


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