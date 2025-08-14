# mcp_client_stdio.py
import os
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any, Tuple
from config import COINGECKO_API_KEY

MCP_URL = "https://mcp.pro-api.coingecko.com/sse"

async def _call_markets(per_page: int = 250, vs_currency: str = "usd") -> List[Dict[str, Any]]:
    if not COINGECKO_API_KEY:
        raise RuntimeError("COINGECKO_API_KEY is not set")

    env = os.environ.copy()
    env.setdefault("MCP_REMOTE_NO_BROWSER", "1")
    env.setdefault("MCP_REMOTE_TRANSPORT", "sse-only")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "mcp-remote@latest", MCP_URL, f"--apiKey={COINGECKO_API_KEY}"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            items = tools.tools or []
            # Searching tool, that will return curent market: get_coins_markets
            wanted = next((t for t in items if t.name.lower() in [
                "get_coins_markets", "coins_markets", "markets", "get_markets"
            ]), None)
            if not wanted:
                # Fallback, will showed other markets if te scheme is different
                raise RuntimeError(f"No markets tool found. Available: {[t.name for t in items]}")

            # Most of all will understandthat ( REST /coins/markets):
            args = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": per_page,   # server limit 250
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h",
            }

            res = await session.call_tool(wanted.name, args)
            blocks = getattr(res, "content", []) or []
            text = "\n".join([b.text for b in blocks if getattr(b, "type", "") == "text"]).strip()
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    return data
                # sometimes MCP can back object with field  data
                if isinstance(data, dict) and isinstance(data.get("data"), list):
                    return data["data"]
                return []
            except Exception:
                # if return not JSON —will return empty 
                return []

def _safe_num(x, key, default=0.0):
    try:
        return float(x.get(key, default) or default)
    except Exception:
        return default

def _norm_token(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": x.get("name") or x.get("id") or "?",
        "symbol": (x.get("symbol") or "").upper(),
        "current_price": _safe_num(x, "current_price"),
        "price_change_percentage_24h": _safe_num(x, "price_change_percentage_24h"),
        "id": x.get("id"),
    }

def _top_gainers_losers(markets: List[Dict[str, Any]], top_n: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows = [_norm_token(r) for r in markets]
    rows = [r for r in rows if r["current_price"] > 0]
    gainers = sorted(rows, key=lambda r: r["price_change_percentage_24h"], reverse=True)[:top_n]
    losers  = sorted(rows, key=lambda r: r["price_change_percentage_24h"])[:top_n]
    return gainers, losers

def _strange_activity(markets: List[Dict[str, Any]], global_change_abs_lt: float = 1.0, top_n: int = 5) -> List[Dict[str, Any]]:
    # Will take strong movements |%| 
    rows = [_norm_token(r) for r in markets]
    rows = [r for r in rows if abs(r["price_change_percentage_24h"]) >= 20][:top_n]
    return rows

def _fomo(gainers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fomo = []
    for t in gainers:
        pct = t["price_change_percentage_24h"]
        if pct >= 20:
            profit = 100 * (pct / 100.0)
            fomo.append({**t, "fomo_100_profit": round(profit, 2), "fomo_100_final": round(100 + profit, 2)})
    return fomo[:3]

async def fetch_mcp_summary(top_n: int = 5, per_page: int = 250) -> Dict[str, Any]:
    markets = await _call_markets(per_page=per_page, vs_currency="usd")
    gainers, losers = _top_gainers_losers(markets, top_n=top_n)
    return {
        "markets_count": len(markets),
        "gainers": gainers,
        "losers": losers,
        "strange": _strange_activity(markets, top_n=top_n),
        "fomo": _fomo(gainers),
        "source": "MCP CoinGecko",
    }

if __name__ == "__main__":
    async def _run():
        out = await fetch_mcp_summary(top_n=5, per_page=250)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    asyncio.run(_run())
