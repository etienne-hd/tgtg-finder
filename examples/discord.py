from api import Bag
from api.logger import logger

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def trigger_webhook(bag: Bag) -> None:
    webhook_url = os.getenv("WEBHOOK_URL")

    # Webhook code here
    payload = {
        "content": f"**{bag.items_available}** basket{'s' if bag.items_available > 1 else ''} available at `{bag.store.name}`",
        "embeds": [
            {
                "description": f"**[Reserve it!](https://share.toogoodtogo.com/item/{bag.item.id})** (only {bag.items_available} left)\n~~{bag.item.value} {bag.item.value_currency}~~  → **{bag.item.price} {bag.item.price_currency}**\n\n```{bag.item.description}```",
                "color": 24670,
                "author": {
                    "name": bag.store.name,
                    "icon_url": bag.store.logo_picture
                },
                "image": {
                    "url": bag.item.cover_picture
                }
            }
        ],
        "username": "TooGoodToGo Finder",
        "avatar_url": "https://raw.githubusercontent.com/etienne-hd/tgtg-finder/refs/heads/main/logo.png",
        "attachments": []
    }

    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        logger.exception(f"Error while sending webhook: {e}")