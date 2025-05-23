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
        self._auth: Auth = None
        self._email = None

    def _init_session(self) -> tls_client.Session:
        session = tls_client.Session('safari_ios_16_0', random_tls_extension_order=True)

        app_version = self.get_app_version()

        session.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'x-correlation-id': str(uuid.uuid4()),
            'accept-language': 'en-GB',
            'user-agent': f'TooGoodToGo/{app_version} (iPhone/iPhone {config.IPHONE_MODEL}; iOS {config.IOS_VERSION}; Scale/2.00/iOS)',
            'accept-encoding': 'gzip, deflate, br'
        }

        return session
    
    def get_app_version(self) -> str:
        response = tls_client.Session("firefox_120").get("https://itunes.apple.com/lookup?bundleId=com.moonsted.TGTG")
        if response.status_code == 200 and response.json()["resultCount"]:
            body = response.json()
            return body["results"][0]["version"]
        
        logger.warning(f"TooGoodToGo version fetch failed ({response.status_code}): {response.text}")
        return "25.5.0"

    def fetch(self, path: str, payload: dict) -> dict:
        logger.debug(f"Sending POST request to '{path}' with payload: {payload}")
        response = self.session.post(f"{config.BASE_URL}{path}", json=payload)
        logger.debug(f"Response received from '{path}': status code = {response.status_code}, response body = {response.text}")

        if response.status_code >= 200 and response.status_code < 300:
            if str(response.text).strip() == "":
                return {}
            return response.json()
        
        if response.status_code == 401:
            raise exception.RequestUnauthorized(f"The request returned a 401 Unauthorized error. This usually means you need to log in before accessing this resource. ({response.text})")
        elif response.status_code == 403:
            raise exception.RequestForbidden(f"The request returned a 403 Forbidden error. This can occur if you send too many requests and Datadome (an anti-bot service) blocks you. ({response.text})")
        elif response.status_code == 429:
            raise exception.RequestTooMany(f"The request returned a 429 Too Many Requests error. You have sent too many requests in a short period. Please slow down and try again later. ({response.text})")
        else:
            raise exception.RequestError(f"An error {response.status_code} has occurred. ({response.text})")

    def is_connected(self) -> bool:
        return self._check_auth(self._auth) if self._auth else False

    @staticmethod
    def require_login(function: Callable):
        def wrapper(*args, **kwargs):
            self = args[0]
            if self._auth is None:
                raise exception.NotAuthenticated(f"The function '{function.__name__}' requires authentication.")

            if time.time() > self._auth.access_token_expiration:
                self._auth = self._refresh_auth(self._auth)

            self.session.headers["authorization"] = f"Bearer {self._auth.access_token}"
            result = function(*args, **kwargs)
            del self.session.headers["authorization"] # Remove auth header to avoid sending it with non-authenticated requests
            return result
        return wrapper
    
    @require_login
    def browse(
        self, search_phrase: str = "", radius: int = 22, 
        favorites_only: bool = False, item_categories: List[ItemCategory] = [], diet_categories: List[DietCategory] = [], 
        page: int = 1, latitude: float = 0, longitude: float = 0, 
        page_size: int = 400, sort_option: SortOption = SortOption.RELEVANCE, with_stock_only: bool = True, 
        hidden_only: bool = False, discover: bool = False
    ) -> List[Bag]:
        bags: List[Bag] = []

        payload = {
            "search_phrase": search_phrase,
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

        body = self.fetch(f"/item/v8/", payload=payload)
        for bag_raw in body["items"]:
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

        body = self.fetch(f"/item/v8/favorites", payload=payload)
        for bag_raw in body["surprise_bags"]:
            bags.append(Bag(raw=bag_raw))

        return bags

    @require_login
    def get_bag(self, item_id: int, longitude: float = 0, latitude: float = 0) -> Bag:
        payload = {
            "origin": {
                "longitude": longitude,
                "latitude": latitude
            }
        }

        body = self.fetch(f"/item/v8/{item_id}", payload=payload)
        return Bag(body)

    @require_login
    def set_favorite(self, bag: Bag) -> None:
        payload = {
            "store_id": str(bag.store.id),
            "is_favorite": True
        }

        self.fetch(f"/user/favorite/v1/{bag.item.id}/update", payload=payload)

    @require_login
    def unset_favorite(self, bag: Bag) -> None:
        payload = {
            "store_id": str(bag.store.id),
            "is_favorite": False
        }

        self.fetch(f"/user/favorite/v1/{bag.item.id}/update", payload=payload)

    def _generate_datadome_cookie(self) -> None:
        payload = {
            "country_code": config.COUNTRY_CODE,
            "uuid": str(uuid.uuid4()),
            "event_type": "BEFORE_COOKIE_CONSENT"
        }

        self.fetch(f"/tracking/v1/anonymousEvents", payload=payload)
        if any(cookie.name == "datadome" for cookie in self.session.cookies):
            logger.info("Successfully generated Datadome cookie.")
            return
        
        raise exception.DatadomeError("Unable to generate Datadome cookie.")

    def _refresh_auth(self, auth: Auth) -> Optional[Auth]:
        payload = {
            "refresh_token": auth.refresh_token
        }

        body = self.fetch(f"/token/v1/refresh", payload=payload)
        auth = Auth(
            access_token=body["access_token"],
            access_token_expiration=body["access_token_ttl_seconds"] + int(time.time()),
            refresh_token=body["refresh_token"]
        )
        logger.info("Successfully refreshed access token.")
        self._save_cookie(email=self._email, cookie=auth)
        return auth
        
    def _check_auth(self, auth: Auth) -> bool:
        self.session.headers["authorization"] = f"Bearer {auth.access_token}"
        try:
            self.fetch("/app/v1/onStartup", payload={})
            return True
        except exception.RequestUnauthorized:
            return False
        except Exception as e:
            raise e
        finally:
            del self.session.headers["authorization"]

    def _auth_by_request_polling_id(self, email: str, polling_id: str) -> Optional[Auth]:
        payload = {
            "request_polling_id": polling_id,
            "device_type": "IOS",
            "email": email
        }

        body = self.fetch(f"/auth/v5/authByRequestPollingId", payload=payload)
        if body != {} and "access_token" in body:
            return Auth(
                access_token=body["access_token"],
                access_token_expiration=body["access_token_ttl_seconds"] + int(time.time()),
                refresh_token=body["refresh_token"]
            )

    def _auth_by_email(self, email: str) -> str:
        payload = {
            "email": email,
            "device_type": "IOS"
        }

        body = self.fetch(f"/auth/v5/authByEmail", payload=payload)
        if body.get("polling_id", None):
            return body["polling_id"]
        
        raise exception.PollingIDError(f"Polling ID could not be retrieved during login. {body}")

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
        self._email = email
        auth: Auth = None
        self._generate_datadome_cookie()

        # Log in via cookie
        if self.use_cookie and (cookie := self._load_cookie(email=email)):
            logger.info("Trying to log in using saved cookie...")
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

        self._auth = auth
        return True
