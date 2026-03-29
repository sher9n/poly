"""Client for fetching events from Polymarket's public APIs."""
import httpx
from datetime import datetime, timedelta
from typing import Optional


GAMMA_API_URL = "https://gamma-api.polymarket.com"


async def fetch_active_events(limit: int = 20) -> list[dict]:
    """Fetch active events that end within the next 7 days."""
    async with httpx.AsyncClient(timeout=30) as client:
        now = datetime.utcnow()
        one_week = now + timedelta(days=7)

        resp = await client.get(
            f"{GAMMA_API_URL}/events",
            params={
                "active": True,
                "closed": False,
                "limit": limit,
                "order": "end_date_iso",
                "ascending": True,
                "end_date_min": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date_max": one_week.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        resp.raise_for_status()
        events = resp.json()

        results = []
        for event in events:
            markets = event.get("markets", [])
            if not markets:
                continue

            for market in markets:
                outcome_prices = market.get("outcomePrices", "")
                if not outcome_prices:
                    continue

                try:
                    # outcomePrices is a JSON string like "[\"0.65\",\"0.35\"]"
                    import json
                    prices = json.loads(outcome_prices)
                    yes_price = float(prices[0]) if prices else 0.5
                except (ValueError, IndexError):
                    yes_price = 0.5

                results.append({
                    "event_id": event.get("id", ""),
                    "condition_id": market.get("conditionId", ""),
                    "question": market.get("question", event.get("title", "")),
                    "description": market.get("description", ""),
                    "category": _categorize(event.get("title", ""), market.get("question", "")),
                    "yes_price": yes_price,
                    "no_price": round(1 - yes_price, 4),
                    "volume": float(market.get("volume", 0) or 0),
                    "liquidity": float(market.get("liquidity", 0) or 0),
                    "end_date": market.get("endDate", event.get("endDate", "")),
                    "image": event.get("image", ""),
                })

        return results


async def fetch_event_by_id(event_id: str) -> Optional[dict]:
    """Fetch a specific event by ID."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{GAMMA_API_URL}/events/{event_id}")
        if resp.status_code != 200:
            return None
        return resp.json()


async def check_resolution(condition_id: str) -> Optional[str]:
    """Check if a market has resolved. Returns 'YES', 'NO', or None."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{GAMMA_API_URL}/markets",
            params={"condition_id": condition_id},
        )
        if resp.status_code != 200:
            return None

        markets = resp.json()
        if not markets:
            return None

        market = markets[0] if isinstance(markets, list) else markets
        if market.get("closed") or market.get("resolved"):
            outcome = market.get("outcome", "")
            if outcome:
                return outcome.upper()

            # Check resolution data
            resolution = market.get("resolution", "")
            if resolution:
                return resolution.upper()

        return None


def _categorize(title: str, question: str) -> str:
    text = (title + " " + question).lower()
    if any(w in text for w in ["election", "president", "vote", "congress", "senate", "trump", "biden", "political"]):
        return "politics"
    if any(w in text for w in ["bitcoin", "ethereum", "crypto", "btc", "eth", "solana", "token"]):
        return "crypto"
    if any(w in text for w in ["nba", "nfl", "mlb", "ufc", "fight", "game", "match", "championship", "super bowl", "world cup"]):
        return "sports"
    if any(w in text for w in ["oscar", "grammy", "movie", "album", "show", "celebrity"]):
        return "entertainment"
    if any(w in text for w in ["stock", "fed", "interest rate", "gdp", "inflation", "s&p", "nasdaq"]):
        return "finance"
    if any(w in text for w in ["space", "nasa", "climate", "ai", "fda", "study"]):
        return "science"
    return "other"
