from .logger import logger
from .client import Client
from .exception import PollingIDError
from .models.cookie import Cookie
import settings

import time
from typing import Optional
import uuid
import os
import tls_client
import json

class TGTG:
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())
        self.session = self.init_session()

    def init_session(self) -> tls_client.Session:
        session = tls_client.Session('firefox_120', random_tls_extension_order=True)

        session.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'x-correlation-id': self.correlation_id,
            'accept-language': 'en-GB',
            'user-agent': 'TooGoodToGo/25.5.0 (227.1) (iPhone/iPhone 11; iOS 18.4; Scale/2.00/iOS)',
        }

        return session

    def _auth_by_request_polling_id(self, email: str, polling_id: str) -> Optional[Cookie]:
        payload = {
            "request_polling_id": polling_id,
            "device_type": settings.DEVICE_TYPE,
            "email": email
        }

        response = self.session.post(f"{settings.BASE_URL}/auth/v5/authByRequestPollingId", json=payload)
        logger.debug(f"text_response: {response.text}; status_code: {response.status_code}; payload: {payload}")
        if response.status_code == 200:
            content: dict = response.json()
            return Cookie(
                access_token=content["access_token"],
                access_token_expiration=content["access_token_ttl_seconds"] + int(time.time()),
                refresh_token=content["refresh_token"]
            )

    def _auth_by_email(self, email: str) -> str:
        payload = {
            "email": email,
            "device_type": settings.DEVICE_TYPE
        }

        response = self.session.post(f"{settings.BASE_URL}/auth/v5/authByEmail", json=payload)
        content: dict = response.json()
        if content.get("polling_id", None):
            return content["polling_id"]
        
        raise PollingIDError(f"Polling ID could not be retrieved during login. {content}")

    def _save_cookie(self, email: str, cookie: Cookie):
        save_path = os.path.join("cookie", f"{email}.json")

        os.makedirs("cookie", exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(cookie.to_json(), f)
        logger.info(f"Cookie successfully saved at '{save_path}'.")

    def _load_cookie(self, email: str) -> Optional[Cookie]:
        save_path = os.path.join("cookie", f"{email}.json")

        if os.path.exists(save_path):
            with open(save_path, "r") as f:
                content = json.load(f)

            logger.info(f"Cookie successfully loaded at '{save_path}'.")
            return Cookie(
                access_token=content["access_token"],
                access_token_expiration=content["access_token_expiration"],
                refresh_token=content["refresh_token"]
            )

    def login(self, email: str, save_cookie: bool = True, use_cookie: bool = True) -> Optional[Client]:
        save_path = os.path.join("cookie", f"{email}.json")

        if os.path.exists(save_path) and use_cookie:
            logger.info("Trying to log in using saved cookie...")
            cookie = self._load_cookie(email=email)
            if cookie:
                return Client(cookie=cookie)
            logger.info("Failed to authenticate with cookie. Falling back to email login.")

        logger.info("Attempting to log in via email...")
        polling_id = self._auth_by_email(email=email)

        start_time = time.time()
        while start_time + settings.POLLING_TIMEOUT > time.time():
            logger.info("Waiting for the user to confirm login via email...")
            cookie = self._auth_by_request_polling_id(email=email, polling_id=polling_id)
            if cookie:
                break
            time.sleep(settings.POLLING_SLEEP_TIME)
        else:
            raise TimeoutError(f"The user did not authorize the connection within {settings.POLLING_TIMEOUT} second(s).")
        
        if save_cookie:
            self._save_cookie(email=email, cookie=cookie)

        return Client(cookie=cookie)