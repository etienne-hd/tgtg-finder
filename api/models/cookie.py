class Cookie:
    def __init__(self, access_token: str, access_token_expiration: str, refresh_token: str):
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration
        self.refresh_token = refresh_token

    def to_json(self):
        return {
            "access_token": self.access_token,
            "access_token_expiration": self.access_token_expiration,
            "refresh_token": self.refresh_token
        }