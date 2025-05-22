class Item:
    def __init__(self, raw: dict):
        self.raw = raw
        self.id: str = raw["item_id"]
        self.price: float = raw["item_price"]["minor_units"] / pow(10, raw["item_price"]["decimals"])
        self.price_currency: str = raw["item_price"]["code"]
        self.value: float = raw["item_value"]["minor_units"] / pow(10, raw["item_value"]["decimals"])
        self.value_currency: float = raw["item_value"]["code"]
        self.cover_picture: str = raw["cover_picture"]["current_url"]
        self.logo_picture: str = raw["logo_picture"]["current_url"]
        self.name: str = raw["name"]
        self.description: str = raw["description"]
        self.item_category: str = raw["item_category"]