from api import TGTG

import os
from dotenv import load_dotenv
def main():
    load_dotenv()
    email = os.getenv("EMAIL")

    api = TGTG()
    client = api.login(email=email, save_cookie=True, use_cookie=True)

if __name__ == "__main__":
    main()