import json, html, datetime as dt
from anthropic import Anthropic
from config import CLAUDE_API_KEY
from analyzer import prepare_report

anth = Anthropic(api_key=CLAUDE_API_KEY)

def _e(x) -> str:
    """Escape HTML for Telegram-safe output."""
    return html.escape(str(x), quote=False)

def _fmt_rows(rows):
    """Format token rows with HTML-safe escaping and \\n breaks."""
    if not rows:
        return "—"
    lines = []
    for r in rows:
        name = _e(r.get("name") or r.get("id") or "?")
        symbol = _e((r.get("symbol") or "").upper())
        pct = float(r.get("pct", r.get("price_change_percentage_24h", 0.0)) or 0.0)
        price = float(r.get("price", r.get("current_price", 0.0)) or 0.0)
        lines.append(f"{name} ({symbol}) | {'+' if pct >= 0 else ''}{pct:.2f}% | ${price:.6f}")
    return "\n".join(lines)

def _today():
    now = dt.datetime.now()
    wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now.weekday()]
    return f"{wd}, {now.strftime('%Y-%m-%d')}"

SYSTEM_PROMPT = (
    "You are Fomo TG Bot: snarky but useful. "
    "Be concise and punchy but never toxic. "
    "Strictly use provided numbers for context; you need to add plausible reasoning/news if widely-known. "
    "Keep outputs no so short but readable."
)

def _build_comment_prompt(data: dict) -> str:
    """
    Ask Claude for JUST comments, returned as compact JSON:
      {
        "fomo": "string <= 180 chars, snarky if pumps, supportive if flat",
        "market_comment": "string <= 220 chars",
        "majors_comment": "string <= 220 chars",
        "gainers_notes": {"SYMBOL": "note <= 80 chars", ...},
        "losers_notes": {"SYMBOL": "note <= 80 chars", ...}
      }
    If unsure, use '—'. No markdown, no tables.
    """
    g_symbols = [ (r.get("symbol") or "").upper() for r in (data.get("gainers") or []) ]
    l_symbols = [ (r.get("symbol") or "").upper() for r in (data.get("losers") or []) ]
    template = {
        "fomo": "",
        "market_comment": "",
        "majors_comment": "",
        "gainers_notes": {s: "" for s in g_symbols},
        "losers_notes": {s: "" for s in l_symbols},
    }
    return (
        "Return ONLY valid JSON matching this exact shape and key set.\n"
        "Lengths: fomo<=180, market_comment<=220, majors_comment<=220, per-token notes<=80.\n"
        "If unsure, put '—'. No markdown, no code fences.\n\n"
        + json.dumps(template, ensure_ascii=False)
        + "\n\nContext data:\n"
        + json.dumps(data, ensure_ascii=False)
    )

def _get_comments(payload: dict) -> dict:
    """Call Claude to get comment JSON; fall back to defaults on failure."""
    prompt = _build_comment_prompt(payload)
    try:
        msg = anth.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=700,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (msg.content[0].text if msg and msg.content else "").strip()
        # Extract JSON if Claude wrapped it
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start:end+1]
        data = json.loads(raw)
        # basic shape sanity
        for key in ["fomo", "market_comment", "majors_comment", "gainers_notes", "losers_notes"]:
            if key not in data:
                data[key] = "—" if key.endswith("comment") or key == "fomo" else {}
        # ensure dicts
        if not isinstance(data.get("gainers_notes"), dict):
            data["gainers_notes"] = {}
        if not isinstance(data.get("losers_notes"), dict):
            data["losers_notes"] = {}
        return data
    except Exception:
        return {
            "fomo": "Market feels range-bound; if you missed a pump, breathe. Monday-mode: on.",
            "market_comment": "Cautious bid persists; liquidity pockets drive selective moves.",
            "majors_comment": "BTC steady, ETH waiting for catalyst, SOL resilient on dips.",
            "gainers_notes": {},
            "losers_notes": {},
        }

def generate_daily_report() -> str:
    D = prepare_report(top_n=5)

    payload = {
        "date": _today(),
        "global": D.get("global"),
        "majors": D.get("majors"),
        "gainers": D.get("gainers")[:5] or [],
        "losers": D.get("losers")[:5] or [],
        "strange": D.get("strange")[:5] or [],
        "fomo": D.get("fomo")[:3] or [],
        "notes": {"global_change_24h": D.get("global_change_24h")},
    }

    comments = _get_comments(payload)
    fomo_txt = _e(comments.get("fomo", "—"))
    market_c = _e(comments.get("market_comment", "—"))
    majors_c = _e(comments.get("majors_comment", "—"))
    g_notes  = { (k or "").upper(): _e(v) for k, v in (comments.get("gainers_notes") or {}).items() if v }
    l_notes  = { (k or "").upper(): _e(v) for k, v in (comments.get("losers_notes") or {}).items() if v }

    g = payload.get("global") or {}
    m = payload.get("majors") or {}

    market_cap = g.get("market_cap_usd", 0)
    vol_usd    = g.get("volume_usd", 0)
    dom_btc    = g.get("btc_dominance_pct", 0.0)
    mkt_chg    = g.get("market_cap_change_24h_pct", 0.0)

    def _mj(key, label):
        row = m.get(key) or {}
        if not row:
            return f"{label}: n/a"
        return (
            f"{label}: "
            f"{'+' if float(row.get('pct_24h', 0)) >= 0 else ''}{float(row.get('pct_24h', 0)):.2f}% "
            f"(${float(row.get('price', 0)):.2f}) "
            f"range ${float(row.get('low_24h', 0)):.0f}-${float(row.get('high_24h', 0)):.0f} "
            f"vol ${float(row.get('volume_24h', 0)):.0f}"
        )

    parts = []

    # 🔥 FOMO & Takeaways (only Claude text)
    parts.append(f"🔥 <b>FOMO & Takeaways</b>\n{fomo_txt}")

    # 📊 Market Overview (our numbers) + 1 comment
    parts.append(
        "📊 <b>Market Overview</b>\n"
        f"Cap ${market_cap:,.0f} | 24h {('+' if mkt_chg >= 0 else '')}{mkt_chg:.2f}% | "
        f"Vol ${vol_usd:,.0f} | BTC dom {dom_btc:.2f}%"
    )
    if market_c and market_c != "—":
        parts.append(f"<i>{market_c}</i>")

    # 🪙 Majors + 1 comment
    parts.append(
        "🪙 <b>Majors</b>\n"
        + _e(_mj("bitcoin", "BTC")) + "\n"
        + _e(_mj("ethereum", "ETH")) + "\n"
        + _e(_mj("solana", "SOL"))
    )
    if majors_c and majors_c != "—":
        parts.append(f"<i>{majors_c}</i>")

    # 🚀 Gainers (table + per-token bullets if present)
    parts.append("🚀 <b>Top Gainers (24h)</b>\n" + _fmt_rows(payload["gainers"]))
    if g_notes:
        lines = []
        for r in payload["gainers"]:
            sym = (r.get("symbol") or "").upper()
            note = g_notes.get(sym)
            if note:
                lines.append(f"• {sym}: {note}")
        if lines:
            parts.append("\n".join(lines))

    # 💀 Losers (table + per-token bullets if present)
    parts.append("💀 <b>Top Losers (24h)</b>\n" + _fmt_rows(payload["losers"]))
    if l_notes:
        lines = []
        for r in payload["losers"]:
            sym = (r.get("symbol") or "").upper()
            note = l_notes.get(sym)
            if note:
                lines.append(f"• {sym}: {note}")
        if lines:
            parts.append("\n".join(lines))

    # 🧐 Strange Activity (table only)
    strange_txt = _fmt_rows(payload["strange"])
    if strange_txt.strip() == "—":
        strange_txt = "None today."
    parts.append("🧐 <b>Strange Activity</b>\n" + strange_txt)

    # no MCP cross-check / no sources badge (per your request)

    return "\n\n".join(parts)
