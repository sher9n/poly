"""Paper trading engine with Kelly Criterion position sizing."""
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Portfolio, Trade, BankrollHistory, TradeStatus


async def get_or_create_portfolio(db: AsyncSession) -> Portfolio:
    result = await db.execute(select(Portfolio).limit(1))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        portfolio = Portfolio(bankroll=1000.0, initial_bankroll=1000.0)
        db.add(portfolio)

        history = BankrollHistory(bankroll=1000.0, event_description="Initial bankroll")
        db.add(history)

        await db.commit()
        await db.refresh(portfolio)
    return portfolio


def calculate_stake(bankroll: float, our_prob: float, market_price: float, max_pct: float = 0.10) -> float:
    """
    Kelly Criterion position sizing.
    f* = (bp - q) / b
    where b = (1/market_price) - 1 (decimal odds minus 1), p = our_prob, q = 1 - p
    Capped at max_pct of bankroll, with a fractional Kelly (25%) for safety.
    """
    if market_price <= 0 or market_price >= 1:
        return 0.0

    b = (1 / market_price) - 1  # net decimal odds
    p = our_prob
    q = 1 - p

    kelly = (b * p - q) / b if b > 0 else 0
    kelly = max(kelly, 0)

    # Use fractional Kelly (25%) for safety
    fraction = 0.25
    kelly_stake = bankroll * kelly * fraction

    # Cap at max_pct of bankroll
    max_stake = bankroll * max_pct
    stake = min(kelly_stake, max_stake)

    # Minimum bet of $5 if there's an edge, skip if less
    if stake < 5:
        return 0.0

    return round(stake, 2)


async def place_trade(
    db: AsyncSession,
    event_id: str,
    condition_id: str,
    question: str,
    category: str,
    predicted_outcome: str,
    our_predicted_probability: float,
    market_price: float,
    research_summary: str,
    research_sources: list[str],
    event_end_date: str = "",
) -> Trade | None:
    """Place a paper trade if there's sufficient edge."""
    portfolio = await get_or_create_portfolio(db)

    # Determine the effective market price based on our prediction
    if predicted_outcome == "YES":
        entry_price = market_price
    else:
        entry_price = 1 - market_price

    edge = our_predicted_probability - entry_price
    if edge <= 0.02:  # Need at least 2% edge
        return None

    stake = calculate_stake(portfolio.bankroll, our_predicted_probability, entry_price)
    if stake == 0:
        return None

    potential_payout = round(stake / entry_price, 2)

    trade = Trade(
        event_id=event_id,
        condition_id=condition_id or "",
        question=question,
        category=category,
        predicted_outcome=predicted_outcome,
        market_price_at_entry=market_price,
        our_predicted_probability=our_predicted_probability,
        edge=round(edge, 4),
        stake=stake,
        potential_payout=potential_payout,
        research_summary=research_summary,
        research_sources=json.dumps(research_sources),
        event_end_date=event_end_date,
        status=TradeStatus.OPEN.value,
    )
    db.add(trade)

    # Deduct stake from bankroll
    portfolio.bankroll = round(portfolio.bankroll - stake, 2)
    portfolio.updated_at = datetime.utcnow()

    # Record bankroll change
    history = BankrollHistory(
        bankroll=portfolio.bankroll,
        event_description=f"Placed trade: {question[:80]} ({predicted_outcome} @ {entry_price:.2f})",
    )
    db.add(history)

    await db.commit()
    await db.refresh(trade)
    return trade


async def resolve_trade(db: AsyncSession, trade: Trade, actual_outcome: str) -> Trade:
    """Resolve a trade and update bankroll."""
    portfolio = await get_or_create_portfolio(db)

    actual_outcome = actual_outcome.upper()
    trade.actual_outcome = actual_outcome
    trade.resolved_at = datetime.utcnow()

    if trade.predicted_outcome == actual_outcome:
        trade.status = TradeStatus.WON.value
        trade.pnl = round(trade.potential_payout - trade.stake, 2)
        portfolio.bankroll = round(portfolio.bankroll + trade.potential_payout, 2)
        portfolio.total_wins += 1
    else:
        trade.status = TradeStatus.LOST.value
        trade.pnl = -trade.stake
        portfolio.total_losses += 1

    portfolio.updated_at = datetime.utcnow()

    history = BankrollHistory(
        bankroll=portfolio.bankroll,
        event_description=f"Resolved: {trade.question[:80]} - {'WON' if trade.status == TradeStatus.WON.value else 'LOST'} (PnL: ${trade.pnl:+.2f})",
    )
    db.add(history)

    await db.commit()
    await db.refresh(trade)
    return trade
