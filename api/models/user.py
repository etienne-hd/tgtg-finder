class User:
    def __init__(self, raw: dict):
        self.raw = raw
        self.id: str = raw["user_id"]
        self.name: str = raw["name"]
        self.country_id: str = raw["country_id"]
        self.email: str = raw["email"]
        self.phone_country_code: str = raw["phone_country_code"]
        self.phone_number: str = raw["phone_number"]
        self.is_partner: bool = raw["is_partner"]
        self.newsletter_opt_in: bool = raw["newsletter_opt_in"]
        self.push_notifications_opt_in: bool = raw["push_notifications_opt_in"]
        self.data_sharing_opt_out: bool = raw["data_sharing_opt_out"]
        self.gender: str = raw["gender"]
        self.user_addresses: list = raw["user_addresses"]