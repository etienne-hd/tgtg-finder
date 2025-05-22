class Store:
    def __init__(self, raw: dict):
        self.raw = raw
        self.id: str = raw["store_id"]
        self.name: str = raw["store_name"]
        self.branch: str = raw["branch"]
        self.description: str = raw["description"]
        self.tax_identifier: str = raw["tax_identifier"]
        self.website: str = raw["tax_identifier"]
        self.country_name: str = raw["store_location"]["address"]["country"]["name"]
        self.country_iso: str = raw["store_location"]["address"]["country"]["iso_code"]
        self.address_line: str = raw["store_location"]["address"]["address_line"]
        self.longitude: float = raw["store_location"]["location"]["longitude"]
        self.latitude: float = raw["store_location"]["location"]["latitude"]
        self.logo_picture: str = raw["logo_picture"]["current_url"]
        self.cover_picture: str = raw["cover_picture"]["current_url"]