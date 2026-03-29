"""FastAPI backend for Polymarket Paper Trader."""
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import init_db, get_db
from .models import Trade, Portfolio, BankrollHistory, TradeStatus
from .polymarket_client import fetch_active_events, check_resolution
from .researcher import research_event
from .trading_engine import get_or_create_portfolio, place_trade, resolve_trade
from .demo_data import get_demo_events


scheduler = AsyncIOScheduler()


async def auto_resolve_trades():
    """Check open trades for resolution."""
    from .database import async_session

    async with async_session() as db:
        result = await db.execute(
            select(Trade).where(Trade.status == TradeStatus.OPEN.value)
        )
        open_trades = result.scalars().all()

        for trade in open_trades:
            if not trade.condition_id:
                continue
            try:
                outcome = await check_resolution(trade.condition_id)
                if outcome:
                    await resolve_trade(db, trade, outcome)
            except Exception:
                continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.add_job(auto_resolve_trades, "interval", minutes=10)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Polymarket Paper Trader", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Portfolio ───────────────────────────────────────────────────────────

@app.get("/api/portfolio")
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    portfolio = await get_or_create_portfolio(db)
    return {
        "bankroll": portfolio.bankroll,
        "initial_bankroll": portfolio.initial_bankroll,
        "total_wins": portfolio.total_wins,
        "total_losses": portfolio.total_losses,
        "profit": round(portfolio.bankroll - portfolio.initial_bankroll, 2),
        "roi": round((portfolio.bankroll - portfolio.initial_bankroll) / portfolio.initial_bankroll * 100, 2),
        "win_rate": round(
            portfolio.total_wins / (portfolio.total_wins + portfolio.total_losses) * 100, 2
        ) if (portfolio.total_wins + portfolio.total_losses) > 0 else 0,
    }


@app.get("/api/portfolio/history")
async def get_portfolio_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BankrollHistory).order_by(BankrollHistory.timestamp)
    )
    history = result.scalars().all()
    return [
        {
            "bankroll": h.bankroll,
            "timestamp": h.timestamp.isoformat(),
            "event": h.event_description,
        }
        for h in history
    ]


@app.post("/api/portfolio/reset")
async def reset_portfolio(db: AsyncSession = Depends(get_db)):
    """Reset the portfolio to initial state."""
    # Delete all trades and history
    await db.execute(select(Trade).execution_options(synchronize_session="fetch"))
    result = await db.execute(select(Trade))
    for trade in result.scalars().all():
        await db.delete(trade)

    result = await db.execute(select(BankrollHistory))
    for h in result.scalars().all():
        await db.delete(h)

    result = await db.execute(select(Portfolio))
    for p in result.scalars().all():
        await db.delete(p)

    await db.commit()

    portfolio = await get_or_create_portfolio(db)
    return {"message": "Portfolio reset", "bankroll": portfolio.bankroll}


# ─── Events ──────────────────────────────────────────────────────────────

@app.get("/api/events")
async def get_events():
    """Fetch active short-term events from Polymarket, falling back to demo data."""
    try:
        events = await fetch_active_events(limit=30)
        if events:
            return events
    except Exception:
        pass
    # Fall back to demo data
    return get_demo_events()


# ─── Research & Trade ────────────────────────────────────────────────────

@app.post("/api/research")
async def research_and_trade(
    event_id: str,
    condition_id: str = "",
    question: str = "",
    category: str = "other",
    yes_price: float = 0.5,
    end_date: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Research an event and optionally place a trade."""
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Run research
    research = await research_event(question, category=category)

    # Determine market price based on prediction
    market_price = yes_price

    # Try to place a trade
    trade = await place_trade(
        db=db,
        event_id=event_id,
        condition_id=condition_id,
        question=question,
        category=category,
        predicted_outcome=research["predicted_outcome"],
        our_predicted_probability=research["confidence"],
        market_price=market_price,
        research_summary=research["summary"],
        research_sources=research["sources"],
        event_end_date=end_date,
    )

    return {
        "research": research,
        "trade_placed": trade is not None,
        "trade": _trade_to_dict(trade) if trade else None,
        "reason": "Insufficient edge or bankroll" if trade is None else "Trade placed",
    }


@app.post("/api/auto-scan")
async def auto_scan_and_trade(db: AsyncSession = Depends(get_db)):
    """Scan all short-term events, research them, and place trades where there's edge."""
    try:
        events = await fetch_active_events(limit=15)
        if not events:
            events = get_demo_events()
    except Exception:
        events = get_demo_events()

    # Skip events we already have open trades for
    existing = await db.execute(
        select(Trade.event_id).where(Trade.status == TradeStatus.OPEN.value)
    )
    existing_ids = {r[0] for r in existing.fetchall()}
    events = [e for e in events if e["event_id"] not in existing_ids]

    results = []

    for event in events[:10]:  # Limit to 10 to avoid timeouts
        try:
            research = await research_event(
                event["question"],
                category=event.get("category", "other"),
            )

            trade = await place_trade(
                db=db,
                event_id=event["event_id"],
                condition_id=event.get("condition_id", ""),
                question=event["question"],
                category=event.get("category", "other"),
                predicted_outcome=research["predicted_outcome"],
                our_predicted_probability=research["confidence"],
                market_price=event["yes_price"],
                research_summary=research["summary"],
                research_sources=research["sources"],
                event_end_date=event.get("end_date", ""),
            )

            results.append({
                "question": event["question"],
                "research": research,
                "trade_placed": trade is not None,
                "trade": _trade_to_dict(trade) if trade else None,
            })
        except Exception as e:
            results.append({
                "question": event["question"],
                "error": str(e),
                "trade_placed": False,
            })

    return {"scanned": len(results), "results": results}


# ─── Trades ──────────────────────────────────────────────────────────────

@app.get("/api/trades")
async def get_trades(
    status: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Get all trades, optionally filtered by status."""
    query = select(Trade).order_by(desc(Trade.created_at))
    if status:
        query = query.where(Trade.status == status)

    result = await db.execute(query)
    trades = result.scalars().all()
    return [_trade_to_dict(t) for t in trades]


@app.get("/api/trades/{trade_id}")
async def get_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return _trade_to_dict(trade)


@app.post("/api/trades/{trade_id}/resolve")
async def manual_resolve(trade_id: int, outcome: str, db: AsyncSession = Depends(get_db)):
    """Manually resolve a trade."""
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.status != TradeStatus.OPEN.value:
        raise HTTPException(status_code=400, detail="Trade already resolved")

    outcome = outcome.upper()
    if outcome not in ("YES", "NO"):
        raise HTTPException(status_code=400, detail="Outcome must be YES or NO")

    trade = await resolve_trade(db, trade, outcome)
    return _trade_to_dict(trade)


@app.post("/api/resolve-all")
async def check_and_resolve(db: AsyncSession = Depends(get_db)):
    """Manually trigger resolution check for all open trades."""
    result = await db.execute(
        select(Trade).where(Trade.status == TradeStatus.OPEN.value)
    )
    open_trades = result.scalars().all()
    resolved = []

    for trade in open_trades:
        if not trade.condition_id:
            continue
        try:
            outcome = await check_resolution(trade.condition_id)
            if outcome:
                trade = await resolve_trade(db, trade, outcome)
                resolved.append(_trade_to_dict(trade))
        except Exception:
            continue

    return {"checked": len(open_trades), "resolved": len(resolved), "trades": resolved}


# ─── Stats ───────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get detailed trading statistics."""
    portfolio = await get_or_create_portfolio(db)

    result = await db.execute(select(Trade))
    all_trades = result.scalars().all()

    # Category breakdown
    categories = {}
    for trade in all_trades:
        cat = trade.category
        if cat not in categories:
            categories[cat] = {"wins": 0, "losses": 0, "open": 0, "pnl": 0}
        if trade.status == TradeStatus.WON.value:
            categories[cat]["wins"] += 1
            categories[cat]["pnl"] += trade.pnl
        elif trade.status == TradeStatus.LOST.value:
            categories[cat]["losses"] += 1
            categories[cat]["pnl"] += trade.pnl
        else:
            categories[cat]["open"] += 1

    total_trades = len(all_trades)
    resolved = [t for t in all_trades if t.status != TradeStatus.OPEN.value]
    open_trades = [t for t in all_trades if t.status == TradeStatus.OPEN.value]

    return {
        "portfolio": {
            "bankroll": portfolio.bankroll,
            "initial_bankroll": portfolio.initial_bankroll,
            "profit": round(portfolio.bankroll - portfolio.initial_bankroll, 2),
            "roi": round((portfolio.bankroll - portfolio.initial_bankroll) / portfolio.initial_bankroll * 100, 2),
        },
        "trades": {
            "total": total_trades,
            "open": len(open_trades),
            "resolved": len(resolved),
            "wins": portfolio.total_wins,
            "losses": portfolio.total_losses,
            "win_rate": round(portfolio.total_wins / len(resolved) * 100, 2) if resolved else 0,
        },
        "open_exposure": round(sum(t.stake for t in open_trades), 2),
        "categories": categories,
    }


def _trade_to_dict(trade: Trade) -> dict:
    if trade is None:
        return {}
    return {
        "id": trade.id,
        "event_id": trade.event_id,
        "condition_id": trade.condition_id,
        "question": trade.question,
        "category": trade.category,
        "predicted_outcome": trade.predicted_outcome,
        "market_price_at_entry": trade.market_price_at_entry,
        "our_predicted_probability": trade.our_predicted_probability,
        "edge": trade.edge,
        "stake": trade.stake,
        "potential_payout": trade.potential_payout,
        "research_summary": trade.research_summary,
        "research_sources": json.loads(trade.research_sources) if trade.research_sources else [],
        "status": trade.status,
        "actual_outcome": trade.actual_outcome,
        "pnl": trade.pnl,
        "resolved_at": trade.resolved_at.isoformat() if trade.resolved_at else None,
        "event_end_date": trade.event_end_date,
        "created_at": trade.created_at.isoformat() if trade.created_at else None,
    }
