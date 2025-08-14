# analyzer.py
from __future__ import annotations
import asyncio
import threading
from typing import Dict, Any, List, Tuple
from coingecko_client import (
    get_top_gainers_losers,
    get_global_change_24h,
    get_markets,
    _get,  # 
)
from mcp_client_stdio import fetch_mcp_summary  # async

# ----------------- utils formating -----------------

def _tok(t: Dict[str, Any]) -> Dict[str, Any]:
    name   = t.get("name") or t.get("id") or "?"
    symbol = (t.get("symbol") or "").upper()
    try:
        pct = float(t.get("price_change_percentage_24h", t.get("pct", 0)) or 0.0)
    except Exception:
        pct = 0.0
    try:
        price = float(t.get("current_price") or t.get("price") or 0.0)
    except Exception:
        price = 0.0
    out = {"name": name, "symbol": symbol, "pct": pct, "price": price}
    if "fomo_100_profit" in t:
        out["fomo_100_profit"] = t["fomo_100_profit"]
    if "fomo_100_final" in t:
        out["fomo_100_final"] = t["fomo_100_final"]
    return out

def _safe(x: Dict[str, Any], k: str, d: float = 0.0) -> float:
    try:
        return float(x.get(k, d) or d)
    except Exception:
        return d

# -----------------  REST -----------------

def get_majors_snapshot(ids: List[str] = ["bitcoin", "ethereum", "solana"]) -> Dict[str, Dict[str, Any]]:
    rows = get_markets(per_page=250, vs_currency="usd", page=1)
    by_id = {r.get("id"): r for r in rows}
    out: Dict[str, Dict[str, Any]] = {}
    for cid in ids:
        r = by_id.get(cid)
        if not r:
            continue
        out[cid] = {
            "name": r.get("name"),
            "symbol": (r.get("symbol") or "").upper(),
            "price": _safe(r, "current_price"),
            "pct_24h": _safe(r, "price_change_percentage_24h"),
            "high_24h": _safe(r, "high_24h"),
            "low_24h": _safe(r, "low_24h"),
            "volume_24h": _safe(r, "total_volume"),
            "market_cap": _safe(r, "market_cap"),
        }
    return out

def get_global_snapshot() -> Dict[str, Any]:
    data = _get("/global")
    d = data.get("data", {}) if isinstance(data, dict) else {}
    mcap = d.get("total_market_cap") or {}
    vol  = d.get("total_volume") or {}
    return {
        "market_cap_usd": float(mcap.get("usd", 0) or 0),
        "volume_usd": float(vol.get("usd", 0) or 0),
        "market_cap_change_24h_pct": float(d.get("market_cap_change_percentage_24h_usd") or 0.0),
        "btc_dominance_pct": float(d.get("market_cap_percentage", {}).get("btc", 0.0) or 0.0),
        "active_cryptocurrencies": d.get("active_cryptocurrencies"),
        "markets": d.get("markets"),
    }

# ----------------- unique request MCP -----------------

def _fetch_mcp_summary_auto(top_n: int = 5, per_page: int = 250) -> Dict[str, Any]:
    
    try:
        loop = asyncio.get_running_loop()
        loop_running = loop.is_running()
    except RuntimeError:
        loop_running = False

    if not loop_running:
        # обычный синхронный контекст
        try:
            return asyncio.run(fetch_mcp_summary(top_n=top_n, per_page=per_page))
        except Exception as e:
            print("MCP summary failed (sync run):", e)
            return {}

    # если уже есть активный loop (aiogram/FastAPI/и т.п.) — уходим в отдельный поток
    holder: Dict[str, Any] = {}

    def _runner():
        try:
            holder["res"] = asyncio.run(fetch_mcp_summary(top_n=top_n, per_page=per_page))
        except Exception as e:
            print("MCP summary failed (thread run):", e)
            holder["res"] = {}

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join(timeout=45)  
    return holder.get("res", {})

# ----------------- main report collect -----------------

def prepare_report(top_n: int = 5) -> Dict[str, Any]:
    # REST baseline
    gain_raw, lose_raw = get_top_gainers_losers(top_n=top_n)
    gain_rest = [_tok(x) for x in gain_raw]
    lose_rest = [_tok(x) for x in lose_raw]
    global_pct = get_global_change_24h()
    majors = get_majors_snapshot()
    global_full = get_global_snapshot()

    # MCP enrichment 
    mcp = _fetch_mcp_summary_auto(top_n=top_n, per_page=250) or {}

    # Use REST if MCP returm empty
    gainers = [ _tok(x) for x in mcp.get("gainers", []) ] or gain_rest
    losers  = [ _tok(x) for x in mcp.get("losers",  []) ] or lose_rest
    strange = [ _tok(x) for x in mcp.get("strange", []) ]

    # FOMO: MCP →  >=20%
    fomo = [ _tok(x) for x in mcp.get("fomo", []) ]
    if not fomo:
        fomo = [t for t in gainers if t["pct"] >= 20][:3]

    return {
        "global_change_24h": global_pct,
        "global": global_full,
        "majors": majors,              # BTC/ETH/SOL
        "gainers": gainers,
        "losers":  losers,
        "strange": strange,
        "fomo":    fomo,
        "mcp":     mcp,
        "sources": {
            "rest": True,
            "mcp":  bool(mcp),
            "mcp_markets_count": mcp.get("markets_count"),
        }
    }
