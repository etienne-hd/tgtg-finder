from api import Client, Bag
from api.logger import logger

import time
import random

def trigger_webhook(bag: Bag):
    logger.info(f"{bag.display_name} - {bag.items_available}")

def main():
    email = "you@example.com"
    client = Client()

    client.login(email=email)
    if not client.is_connected:
        logger.warning("Client login failed: not connected.")
        return
    
    logger.info("Client successfully connected. Starting favorite bag monitoring...")

    while True:
        try:
            bags = client.get_favorites()
            logger.info(f"Retrieved {len(bags)} favorite bags.")

            for bag in bags:
                if bag.items_available > 0:
                    trigger_webhook(bag=bag)
        except Exception as e:
            logger.exception(f"Error while retrieving favorite bags: {e}")
            time.sleep(60)
        time.sleep(random.randint(30, 60)) # Recommended time to avoid 403 errors

if __name__ == "__main__":
    main()