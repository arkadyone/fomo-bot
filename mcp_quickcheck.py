# That checker is not needed if you use stdio client for MCP 

import os, asyncio, json, glob
from mcp import ClientSession
from mcp.client.sse import sse_client  #  `mcp`
from config import COINGECKO_API_KEY

MCP_URL = "https://mcp.pro-api.coingecko.com/sse"
API_KEY = COINGECKO_API_KEY  # или os.getenv("COINGECKO_API_KEY")

def load_bearer_token() -> str:
    """
   
    """
    base_dir = os.path.expanduser("~/.mcp-auth")
    if not os.path.isdir(base_dir):
        raise RuntimeError("~/.mcp-auth not found.")

    files = glob.glob(os.path.join(base_dir, "**", "*.json"), recursive=True)
    if not files:
        raise RuntimeError("В ~/.mcp-auth no json files with token")

    for path in files:
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception:
            continue

        issuer = (data.get("issuer") or data.get("server") or "").lower()
        if "coingecko" in issuer or "mcp.pro-api.coingecko.com" in issuer:
            # other variants of token storage
            token = (
                data.get("access_token")
                or data.get("token")
                or (data.get("tokens") or {}).get("access_token")
            )
            if token:
                return token

    # fallback: check *_tokens.json
    for path in files:
        if path.endswith("_tokens.json"):
            try:
                data = json.load(open(path))
                token = data.get("access_token") or (data.get("tokens") or {}).get("access_token")
                if token:
                    return token
            except Exception:
                pass

    raise RuntimeError("Bearer token for CoinGecko MCP not found in в ~/.mcp-auth/**.json")

async def main():
    if not API_KEY:
        raise RuntimeError("COINGECKO_API_KEY not setted (in .env .")

    bearer = load_bearer_token()
    headers = {
        "authorization": f"Bearer {bearer}",
        "x-cg-pro-api-key": API_KEY,
    }

    async with sse_client(MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = [t.name for t in (tools.tools or [])]
            print("TOOLS:", tool_names)

            wanted = next(
                (n for n in tool_names if any(k in n.lower() for k in
                                              ["query", "search", "coingecko", "market", "gainers", "losers"])),
                None
            )
            if not wanted:
                print("ПNo tool founded.")
                return

            prompt = ('Return ONLY compact JSON (no markdown): '
                      '{"gainers":[{"name":"","symbol":"","current_price":0,"price_change_percentage_24h":0}],'
                      '"losers":[{"name":"","symbol":"","current_price":0,"price_change_percentage_24h":0}]} '
                      'for the last 24h.')

            res = await session.call_tool(wanted, arguments={"text": prompt, "prompt": prompt, "query": prompt})
            blocks = getattr(res, "content", []) or []
            text = "\n".join([b.text for b in blocks if getattr(b, "type", "") == "text"]).strip()

            try:
                print(json.dumps(json.loads(text), ensure_ascii=False, indent=2))
            except Exception:
                print(text)

if __name__ == "__main__":
    asyncio.run(main())
