from .logger import logger
from .models.auth import Auth
from .models.bag import Bag
from .models.enums import SortOption, ItemCategory, DietCategory
import config
from . import exception

import time
from typing import Optional, Callable, List
import uuid
import os
import tls_client
import json

class Client:
    def __init__(self, save_cookie=True, use_cookie=True):
        self.save_cookie = save_cookie
        self.use_cookie = use_cookie
        self.session = self._init_session()
        self.auth: Auth = None

    def _init_session(self) -> tls_client.Session:
        session = tls_client.Session('safari_ios_16_0', random_tls_extension_order=True)

        session.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'x-correlation-id': str(uuid.uuid4()),
            'accept-language': 'en-GB',
            'user-agent': 'TooGoodToGo/25.5.0 (227.1) (iPhone/iPhone 11; iOS 18.4; Scale/2.00/iOS)',
            'accept-encoding': 'gzip, deflate, br'
        }

        return session

    @staticmethod
    def require_login(function: Callable):
        def wrapper(*args, **kwargs):
            self = args[0]
            if self.auth is None:
                raise exception.NotAuthenticated(f"The function '{function.__name__}' requires authentication.")

            if time.time() > self.auth.access_token_expiration:
                self.auth = self._refresh_auth(self.auth)

            self.session.headers["authorization"] = f"Bearer {self.auth.access_token}"
            result = function(*args, **kwargs)
            del self.session.headers["authorization"] # Remove auth header to avoid sending it with non-authenticated requests
            return result
        return wrapper
    
    @require_login
    def browse(
        self, radius: int = 22, favorites_only: bool = False, 
        item_categories: List[ItemCategory] = [], diet_categories: List[DietCategory] = [], page: int = 1, 
        latitude: float = 0, longitude: float = 0, page_size: int = 400, 
        sort_option: SortOption = SortOption.RELEVANCE, with_stock_only: bool = True, hidden_only: bool = False, 
        discover: bool = False
    ) -> List[Bag]:
        bags: List[Bag] = []

        payload = {
            "radius": radius,
            "favorites_only": favorites_only,
            "item_categories": [category.value for category in item_categories],
            "diet_categories": [category.value for category in diet_categories],
            "page": page,
            "origin": {
                "latitude": latitude,
                "longitude": longitude
            },
            "page_size": page_size,
            "sort_option": sort_option.value,
            "with_stock_only": with_stock_only,
            "hidden_only": hidden_only,
            "discover": discover
        }
        response = self.session.post(f"{config.BASE_URL}/item/v8/", json=payload)
        print(response.status_code, response.text)
        if response.status_code == 200:
            for bag_raw in response.json()["items"]:
                bags.append(Bag(raw=bag_raw))

        return bags
    @require_login
    def get_favorites(
        self, page: int = 0, size: int = 50, 
        latitude: int = 0, longitude: int = 0
    ) -> List[Bag]:
        bags: List[Bag] = []

        payload = {
            "paging":{
                "page": page,
                "size": size
            },
            "origin":{
                "latitude": latitude,
                "longitude": longitude
            }
        }

        response = self.session.post(f"{config.BASE_URL}/item/v8/favorites", json=payload)
        if response.status_code == 200:
            for bag_raw in response.json()["surprise_bags"]:
                bags.append(Bag(raw=bag_raw))
        print(response.status_code)
        
        return bags

    def _generate_datadome_cookie(self) -> None:
        payload = {
            "country_code": config.COUNTRY_CODE,
            "uuid": str(uuid.uuid4()),
            "event_type": "BEFORE_COOKIE_CONSENT"
        }

        response = self.session.post(f"{config.BASE_URL}/tracking/v1/anonymousEvents", json=payload)
        if any(cookie.name == "datadome" for cookie in response.cookies):
            logger.info("Successfully generated Datadome cookie.")
            return
        
        raise exception.DatadomeError("Unable to generate Datadome cookie.")

    def _refresh_auth(self, auth: Auth) -> Optional[Auth]:
        payload = {
            "refresh_token": auth.refresh_token
        }

        response = self.session.post(f"{config.BASE_URL}/token/v1/refresh", json=payload)
        if response.status_code == 200:
            logger.info("Successfully refreshed access token.")
            content = response.json()
            return Auth(
                access_token=content["access_token"],
                access_token_expiration=content["access_token_ttl_seconds"] + int(time.time()),
                refresh_token=content["refresh_token"]
            )
        
        raise exception.TokenRefreshError(f"Failed to refresh access token. Status code: {response.status_code}, Response: {response.text}")

    def _check_auth(self, auth: Auth) -> bool:
        self.session.headers["authorization"] = f"Bearer {auth.access_token}"
        response = self.session.post("https://apptoogoodtogo.com/api/app/v1/onStartup", json={})
        del self.session.headers["authorization"] # Remove auth header to avoid sending it with non-authenticated requests

        if response.status_code == 200:
            return True
        
        return False

    def _auth_by_request_polling_id(self, email: str, polling_id: str) -> Optional[Auth]:
        payload = {
            "request_polling_id": polling_id,
            "device_type": config.DEVICE_TYPE,
            "email": email
        }

        response = self.session.post(f"{config.BASE_URL}/auth/v5/authByRequestPollingId", json=payload)
        logger.debug(f"text_response: {response.text}; status_code: {response.status_code}; payload: {payload}")
        if response.status_code == 200:
            content: dict = response.json()
            return Auth(
                access_token=content["access_token"],
                access_token_expiration=content["access_token_ttl_seconds"] + int(time.time()),
                refresh_token=content["refresh_token"]
            )

    def _auth_by_email(self, email: str) -> str:
        payload = {
            "email": email,
            "device_type": config.DEVICE_TYPE
        }

        response = self.session.post(f"{config.BASE_URL}/auth/v5/authByEmail", json=payload)
        content: dict = response.json()
        if content.get("polling_id", None):
            return content["polling_id"]
        
        raise exception.PollingIDError(f"Polling ID could not be retrieved during login. {content}")

    def _save_cookie(self, email: str, cookie: Auth):
        save_path = os.path.join("cookie", f"{email}.json")

        os.makedirs("cookie", exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(cookie.to_json(), f, indent=4)
        logger.info(f"Cookie successfully saved at '{save_path}'.")

    def _load_cookie(self, email: str) -> Optional[Auth]:
        save_path = os.path.join("cookie", f"{email}.json")

        if os.path.exists(save_path):
            with open(save_path, "r") as f:
                content = json.load(f)

            logger.info(f"Cookie successfully loaded at '{save_path}'.")
            return Auth(
                access_token=content["access_token"],
                access_token_expiration=content["access_token_expiration"],
                refresh_token=content["refresh_token"]
            )
    
    def login(self, email: str) -> bool:
        save_path = os.path.join("cookie", f"{email}.json")
        auth: Auth = None

        # Log in via cookie
        if os.path.exists(save_path) and self.use_cookie:
            logger.info("Trying to log in using saved cookie...")
            cookie = self._load_cookie(email=email)
            if cookie:
                if time.time() > cookie.access_token_expiration:
                    cookie = self._refresh_auth(auth=cookie)
                
                if self._check_auth(cookie):
                    logger.info("Successfully connected using cookie.")
                    auth = cookie
            
            if auth is None:
                logger.info("Failed to authenticate with cookie.")

        # Log in via email
        if auth is None:
            logger.info("Attempting to log in via email...")
            polling_id = self._auth_by_email(email=email)

            start_time = time.time()
            while start_time + config.POLLING_TIMEOUT > time.time():
                logger.info("Waiting for the user to confirm login via email...")
                auth = self._auth_by_request_polling_id(email=email, polling_id=polling_id)
                if auth:
                    logger.info("Successfully connected using email.")
                    break
                time.sleep(config.POLLING_SLEEP_TIME)
            else:
                raise exception.LoginTimeout(f"The user did not authorize the connection within {config.POLLING_TIMEOUT} second(s).")
        
        if self.save_cookie:
            self._save_cookie(email=email, cookie=auth)

        self.auth = auth
        return True
