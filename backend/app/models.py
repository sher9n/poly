from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .database import Base


class TradeStatus(str, enum.Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"


class EventCategory(str, enum.Enum):
    POLITICS = "politics"
    SPORTS = "sports"
    CRYPTO = "crypto"
    ENTERTAINMENT = "entertainment"
    SCIENCE = "science"
    FINANCE = "finance"
    OTHER = "other"


class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bankroll: Mapped[float] = mapped_column(Float, default=1000.0)
    initial_bankroll: Mapped[float] = mapped_column(Float, default=1000.0)
    total_wins: Mapped[int] = mapped_column(Integer, default=0)
    total_losses: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Polymarket event info
    event_id: Mapped[str] = mapped_column(String(256))
    condition_id: Mapped[str] = mapped_column(String(256), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), default=EventCategory.OTHER.value)

    # Trade details
    predicted_outcome: Mapped[str] = mapped_column(String(8))  # "YES" or "NO"
    market_price_at_entry: Mapped[float] = mapped_column(Float)  # price when we entered
    our_predicted_probability: Mapped[float] = mapped_column(Float)  # our confidence
    edge: Mapped[float] = mapped_column(Float)  # predicted_prob - market_price
    stake: Mapped[float] = mapped_column(Float)  # how much we bet
    potential_payout: Mapped[float] = mapped_column(Float)  # stake / market_price

    # Research
    research_summary: Mapped[str] = mapped_column(Text, nullable=True)
    research_sources: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list

    # Resolution
    status: Mapped[str] = mapped_column(String(16), default=TradeStatus.OPEN.value)
    actual_outcome: Mapped[str] = mapped_column(String(8), nullable=True)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Timestamps
    event_end_date: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BankrollHistory(Base):
    __tablename__ = "bankroll_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bankroll: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_description: Mapped[str] = mapped_column(Text, nullable=True)
