# coingecko_client.py
from __future__ import annotations
import os
import requests
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
BASE = "https://pro-api.coingecko.com/api/v3"

_session = requests.Session()
_session.headers.update({
    "Accept": "application/json",
    "x-cg-pro-api-key": COINGECKO_API_KEY or "",
    "User-Agent": "cg-tg-bot/1.0"
})

def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{BASE}{path}"
    r = _session.get(url, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def get_markets(per_page: int = 250, vs_currency: str = "usd", page: int = 1) -> List[Dict[str, Any]]:
    """
    
    """
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "24h",
        "locale": "en"
    }
    data = _get("/coins/markets", params)
    if isinstance(data, list):
        return data
    return []

def get_top_gainers_losers(top_n: int = 5, per_page: int = 250, vs_currency: str = "usd"
                           ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
  
    """
    rows = get_markets(per_page=per_page, vs_currency=vs_currency, page=1)

    def norm(x: Dict[str, Any]) -> Dict[str, Any]:
        def f(key, default=0.0):
            try:
                return float(x.get(key, default) or default)
            except Exception:
                return default
        return {
            "name": x.get("name") or x.get("id") or "?",
            "symbol": (x.get("symbol") or "").upper(),
            "current_price": f("current_price"),
            "price_change_percentage_24h": f("price_change_percentage_24h"),
            "id": x.get("id")
        }

    rows = [norm(x) for x in rows if (x.get("current_price") or 0) not in (None, 0)]
    gainers = sorted(rows, key=lambda r: r["price_change_percentage_24h"], reverse=True)[:top_n]
    losers  = sorted(rows, key=lambda r: r["price_change_percentage_24h"])[:top_n]
    return gainers, losers

def get_global_change_24h() -> Optional[float]:
    """
    .
    """
    try:
        data = _get("/global")
        m = data.get("data", {})
        val = m.get("market_cap_change_percentage_24h_usd")
        if val is None:
            return None
        return float(val)
    except Exception:
        return None
