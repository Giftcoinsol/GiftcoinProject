from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Raffle(Base):
    """
    Таблица раффлов (для логики, отчётов, истории).
    В проекте можно иметь один активный раффл (ACTIVE_RAFFLE_ID),
    остальные — для истории/админки.
    """
    __tablename__ = "raffles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    winners = relationship("RaffleWinner", back_populates="raffle")


class Participant(Base):
    """
    Глобальный список участников.
    Один кошелёк → одна строка.
    Участвует во всех раффлах по умолчанию.
    """
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    wallet = Column(String, nullable=False, unique=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class RaffleWinner(Base):
    """
    История победителей: кто выиграл, в каком раффле, сколько получил, какая транзакция.
    """
    __tablename__ = "raffle_winners"

    id = Column(Integer, primary_key=True, index=True)
    raffle_id = Column(Integer, ForeignKey("raffles.id"), nullable=False)
    wallet = Column(String, nullable=False)
    amount_lamports = Column(BigInteger, nullable=False)
    tx_signature = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    raffle = relationship("Raffle", back_populates="winners")
