from api import Client

import os
from dotenv import load_dotenv
def main():
    load_dotenv()
    email = os.getenv("EMAIL")

    client = Client(save_cookie=True, use_cookie=True)
    client.login(email=email)
    client._generate_datadome_cookie()
    bags = client.get_favorites()
    for bag in bags:
        print(bag.display_name)

if __name__ == "__main__":
    main()