"""Minimal Meta Marketing API client for the TW creative roadmap.

Read-only by design: the routines in this repo never write to Meta, so this client
only exposes GET helpers. Configuration comes from environment variables (see
.env.example); ``load_config()`` reads ``meta_api/.env`` if python-dotenv is installed.

Usage:
    from meta_client import MetaClient, load_config
    client = MetaClient(**load_config())
    for ad in client.get_ads():
        print(ad["id"], ad["name"], ad["effective_status"])
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import requests

GRAPH_BASE = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v21.0"

# Ad-level fields the nightly sync (routine1 step 2) needs.
AD_FIELDS = "id,name,effective_status,created_time,campaign_id,campaign{name},adset_id"

# Insights fields used for spend / frequency checks.
INSIGHT_FIELDS = "ad_id,ad_name,spend,impressions,clicks,frequency,reach"

# Graph API error codes that are safe to retry.
_RETRYABLE_CODES = {1, 2, 4, 17, 32, 613}  # unknown, service, app/user/page rate limits


class MetaAPIError(RuntimeError):
    """Raised for non-retryable Graph API errors. Carries the decoded error body."""

    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None,
                 body: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.body = body or {}


def load_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return client kwargs from META_* env vars, loading meta_api/.env first if present."""
    env_path = env_path or Path(__file__).with_name(".env")
    if env_path.exists():
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(env_path, override=False)
        except ImportError:  # dotenv is optional; fall back to a tiny parser
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    account = os.environ.get("META_AD_ACCOUNT_ID", "").strip()
    if not token:
        raise SystemExit("META_ACCESS_TOKEN is not set. Copy meta_api/.env.example to meta_api/.env and fill it in.")
    if not account:
        raise SystemExit("META_AD_ACCOUNT_ID is not set.")
    return {
        "access_token": token,
        "ad_account_id": account,
        "app_secret": os.environ.get("META_APP_SECRET", "").strip() or None,
        "api_version": os.environ.get("META_API_VERSION", DEFAULT_API_VERSION).strip() or DEFAULT_API_VERSION,
    }


@dataclass
class MetaClient:
    access_token: str
    ad_account_id: str
    app_secret: Optional[str] = None
    api_version: str = DEFAULT_API_VERSION
    timeout: float = 60.0
    max_retries: int = 4
    session: requests.Session = field(default_factory=requests.Session, repr=False)

    # ------------------------------------------------------------------ core

    @property
    def account_path(self) -> str:
        acct = self.ad_account_id
        return acct if acct.startswith("act_") else f"act_{acct}"

    def _auth_params(self) -> Dict[str, str]:
        params = {"access_token": self.access_token}
        if self.app_secret:
            proof = hmac.new(self.app_secret.encode(), self.access_token.encode(), hashlib.sha256).hexdigest()
            params["appsecret_proof"] = proof
        return params

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET one Graph API resource with retry on transient / rate-limit errors."""
        url = path if path.startswith("http") else f"{GRAPH_BASE}/{self.api_version}/{path.lstrip('/')}"
        query = {**(params or {}), **self._auth_params()}
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url, params=query, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = exc
                self._sleep(attempt)
                continue

            if resp.status_code == 200:
                return resp.json()

            try:
                body = resp.json()
            except ValueError:
                body = {"error": {"message": resp.text[:500]}}
            err = body.get("error", {})
            code = err.get("code")
            if code in _RETRYABLE_CODES and attempt < self.max_retries:
                last_error = MetaAPIError(err.get("message", "retryable error"), code, err.get("error_subcode"), body)
                self._sleep(attempt)
                continue
            raise MetaAPIError(
                f"Graph API {resp.status_code} on {path}: {err.get('message')} "
                f"(code={code}, subcode={err.get('error_subcode')}, type={err.get('type')})",
                code, err.get("error_subcode"), body,
            )
        raise MetaAPIError(f"Gave up after {self.max_retries} retries on {path}: {last_error}")

    def paginate(self, path: str, params: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """Yield every item across Graph API cursor pagination."""
        params = dict(params or {})
        params.setdefault("limit", 200)
        page = self.get(path, params)
        while True:
            for item in page.get("data", []):
                yield item
            next_url = page.get("paging", {}).get("next")
            if not next_url:
                return
            # ``next`` already carries the query string + token; do not re-append params.
            page = self.get(next_url, {})

    @staticmethod
    def _sleep(attempt: int) -> None:
        time.sleep(min(2 ** attempt, 30))

    # --------------------------------------------------------------- helpers

    def me(self) -> Dict[str, Any]:
        """Identity behind the token. For a System User this returns the system user's id/name."""
        return self.get("me", {"fields": "id,name"})

    def debug_token(self, app_id: str) -> Dict[str, Any]:
        """Token metadata (scopes, expiry). Requires app id + secret in the app access token form."""
        if not self.app_secret:
            raise MetaAPIError("debug_token needs META_APP_SECRET")
        return self.get("debug_token", {
            "input_token": self.access_token,
            "access_token": f"{app_id}|{self.app_secret}",
        })

    def account(self) -> Dict[str, Any]:
        return self.get(self.account_path, {
            "fields": "id,name,account_status,currency,timezone_name,business{id,name}",
        })

    def get_ads(self, effective_status: Optional[List[str]] = None,
                fields: str = AD_FIELDS) -> List[Dict[str, Any]]:
        """All ads in the account. Pass effective_status=["ACTIVE"] for the live set."""
        params: Dict[str, Any] = {"fields": fields}
        if effective_status:
            params["effective_status"] = _json_list(effective_status)
        return list(self.paginate(f"{self.account_path}/ads", params))

    def get_ad(self, ad_id: str, fields: str = AD_FIELDS) -> Dict[str, Any]:
        """Direct fetch of one ad — used to individually verify an ad is really inactive."""
        return self.get(ad_id, {"fields": fields})

    def get_ad_insights(self, date_preset: str = "maximum", level: str = "ad",
                        fields: str = INSIGHT_FIELDS, ad_ids: Optional[List[str]] = None,
                        time_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Insights at ad level. ``date_preset`` examples: maximum, last_7d, last_30d, yesterday.

        Pass ``time_range={"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}`` instead of a
        preset for an explicit window. ``ad_ids`` narrows the result via a filter.
        """
        params: Dict[str, Any] = {"level": level, "fields": fields}
        if time_range:
            params["time_range"] = _json_obj(time_range)
        else:
            params["date_preset"] = date_preset
        if ad_ids:
            params["filtering"] = _json_list_of_obj([
                {"field": "ad.id", "operator": "IN", "value": ad_ids}
            ])
        return list(self.paginate(f"{self.account_path}/insights", params))

    def get_campaigns(self, fields: str = "id,name,effective_status,objective,created_time") -> List[Dict[str, Any]]:
        return list(self.paginate(f"{self.account_path}/campaigns", {"fields": fields}))


# ------------------------------------------------------------------ utilities

def _json_list(values: List[str]) -> str:
    import json
    return json.dumps(values)


def _json_obj(obj: Dict[str, Any]) -> str:
    import json
    return json.dumps(obj)


def _json_list_of_obj(objs: List[Dict[str, Any]]) -> str:
    import json
    return json.dumps(objs)
