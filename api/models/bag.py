from .item import Item
from .store import Store

class Bag:
    def __init__(self, raw: dict):
        self.raw = raw
        self.display_name: str = raw["display_name"]
        self.items_available: int = raw["items_available"]
        self.item = Item(raw["item"])
        self.store = Store(raw["store"])