"""Demo data for when the Polymarket API is unreachable."""

import random
from datetime import datetime, timedelta

DEMO_EVENTS = [
    {
        "event_id": "demo-1",
        "condition_id": "demo-cond-1",
        "question": "Will Bitcoin exceed $100,000 by end of week?",
        "description": "Resolves YES if BTC price exceeds $100,000 at any point before Sunday 11:59 PM ET.",
        "category": "crypto",
        "yes_price": 0.42,
        "no_price": 0.58,
        "volume": 2_450_000,
        "liquidity": 380_000,
        "end_date": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-2",
        "condition_id": "demo-cond-2",
        "question": "Will the Fed announce an interest rate cut this week?",
        "description": "Resolves YES if the Federal Reserve announces a rate cut at the upcoming FOMC meeting.",
        "category": "finance",
        "yes_price": 0.15,
        "no_price": 0.85,
        "volume": 5_100_000,
        "liquidity": 720_000,
        "end_date": (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-3",
        "condition_id": "demo-cond-3",
        "question": "Will SpaceX successfully launch Starship this week?",
        "description": "Resolves YES if SpaceX conducts a successful Starship launch before Sunday.",
        "category": "science",
        "yes_price": 0.68,
        "no_price": 0.32,
        "volume": 1_800_000,
        "liquidity": 290_000,
        "end_date": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-4",
        "condition_id": "demo-cond-4",
        "question": "Will any team score 150+ points in an NBA game this week?",
        "description": "Resolves YES if any NBA team scores 150 or more points in a single game this week.",
        "category": "sports",
        "yes_price": 0.22,
        "no_price": 0.78,
        "volume": 890_000,
        "liquidity": 150_000,
        "end_date": (datetime.utcnow() + timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-5",
        "condition_id": "demo-cond-5",
        "question": "Will Trump sign a new executive order this week?",
        "description": "Resolves YES if President Trump signs at least one new executive order before Sunday.",
        "category": "politics",
        "yes_price": 0.82,
        "no_price": 0.18,
        "volume": 3_200_000,
        "liquidity": 510_000,
        "end_date": (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-6",
        "condition_id": "demo-cond-6",
        "question": "Will Ethereum flip above $4,000 this week?",
        "description": "Resolves YES if ETH price exceeds $4,000 at any point before Sunday.",
        "category": "crypto",
        "yes_price": 0.31,
        "no_price": 0.69,
        "volume": 1_600_000,
        "liquidity": 240_000,
        "end_date": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-7",
        "condition_id": "demo-cond-7",
        "question": "Will S&P 500 close above 5,800 on Friday?",
        "description": "Resolves YES if S&P 500 closing price on Friday exceeds 5,800.",
        "category": "finance",
        "yes_price": 0.55,
        "no_price": 0.45,
        "volume": 4_300_000,
        "liquidity": 680_000,
        "end_date": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-8",
        "condition_id": "demo-cond-8",
        "question": "Will a major tech company announce layoffs this week?",
        "description": "Resolves YES if any FAANG+ company announces layoffs of 500+ employees.",
        "category": "finance",
        "yes_price": 0.35,
        "no_price": 0.65,
        "volume": 920_000,
        "liquidity": 180_000,
        "end_date": (datetime.utcnow() + timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-9",
        "condition_id": "demo-cond-9",
        "question": "Will there be a ceasefire agreement in any active conflict this week?",
        "description": "Resolves YES if an official ceasefire agreement is announced in any major ongoing conflict.",
        "category": "politics",
        "yes_price": 0.12,
        "no_price": 0.88,
        "volume": 2_100_000,
        "liquidity": 340_000,
        "end_date": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
    {
        "event_id": "demo-10",
        "condition_id": "demo-cond-10",
        "question": "Will UFC 315 main event go the distance?",
        "description": "Resolves YES if the UFC 315 main event fight goes to decision (all rounds completed).",
        "category": "sports",
        "yes_price": 0.38,
        "no_price": 0.62,
        "volume": 750_000,
        "liquidity": 120_000,
        "end_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": "",
    },
]


def get_demo_events() -> list[dict]:
    """Return demo events with slightly randomized prices to simulate live market."""
    events = []
    for e in DEMO_EVENTS:
        event = dict(e)
        # Add slight price variation
        noise = random.uniform(-0.03, 0.03)
        event["yes_price"] = round(max(0.05, min(0.95, event["yes_price"] + noise)), 2)
        event["no_price"] = round(1 - event["yes_price"], 2)
        events.append(event)
    return events
