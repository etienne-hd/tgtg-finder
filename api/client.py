from .models.cookie import Cookie

class Client:
    def __init__(self, cookie: Cookie):
        self.cookie = cookie