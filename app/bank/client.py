"""Small client for the Enable Banking API."""
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import requests

API = "https://api.enablebanking.com"


class BankError(Exception):
    def __init__(self, status: int, body: str):
        self.status, self.body = status, body
        try:
            import json
            data = json.loads(body)
            self.code = data.get("error") or data.get("code") or ""
            self.message = data.get("message") or body
        except Exception:
            self.code, self.message = "", body
        super().__init__(f"{status} {self.code}: {self.message}")


class EnableBanking:
    def __init__(self, app_id: str, private_key: str):
        self.app_id, self.private_key = app_id, private_key
        self._token, self._token_exp = None, 0

    def _auth_header(self) -> dict:
        """A signed JWT proves the request comes from our app. Renewed every ~50 min."""
        now = int(time.time())
        if not self._token or now > self._token_exp - 600:
            self._token_exp = now + 3600
            payload = {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": now, "exp": self._token_exp}
            self._token = jwt.encode(payload, self.private_key, algorithm="RS256", headers={"kid": self.app_id})
        return {"Authorization": f"Bearer {self._token}"}

    def request(self, method: str, path: str, **kwargs) -> dict:
        r = requests.request(method, API + path, headers=self._auth_header(), timeout=60, **kwargs)
        if not r.ok:
            raise BankError(r.status_code, r.text)
        return r.json()

    # --- Banks and login ---
    def aspsps(self, country: str) -> list[dict]:
        return self.request("GET", "/aspsps", params={"country": country}).get("aspsps", [])

    def start_auth(self, aspsp: dict, redirect_url: str, days: int) -> tuple[str, str]:
        state = str(uuid.uuid4())
        body = {
            "access": {"valid_until": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()},
            "aspsp": {"name": aspsp["name"], "country": aspsp["country"]},
            "state": state, "redirect_url": redirect_url, "psu_type": "personal",
        }
        return self.request("POST", "/auth", json=body)["url"], state

    def create_session(self, code: str) -> dict:
        return self.request("POST", "/sessions", json={"code": code})

    def get_session(self, session_id: str) -> dict:
        return self.request("GET", f"/sessions/{session_id}")

    # --- Account data ---
    def balances(self, uid: str) -> dict:
        return self.request("GET", f"/accounts/{uid}/balances")

    def transactions(self, uid: str, date_from: str | None = None, strategy: str | None = None) -> list[dict]:
        """All transactions, following the pages the bank sends back."""
        base = {k: v for k, v in {"date_from": date_from, "strategy": strategy}.items() if v}
        params, result = dict(base), []
        while True:
            page = self.request("GET", f"/accounts/{uid}/transactions", params=params)
            result.extend(page.get("transactions") or [])
            key = page.get("continuation_key")
            if not key:
                return result
            params = {**base, "continuation_key": key}
