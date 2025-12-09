from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models


def get_active_raffle(db: Session, raffle_id: int) -> models.Raffle | None:
    return (
        db.query(models.Raffle)
        .filter(
            models.Raffle.id == raffle_id,
            models.Raffle.is_active == True,
        )
        .first()
    )


def add_participant(db: Session, wallet: str) -> models.Participant:
    """
    Добавляем кошелёк в глобальный список участников.
    Один кошелёк = одна строка (UNIQUE).
    """
    participant = models.Participant(wallet=wallet)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def get_random_participant(db: Session) -> models.Participant | None:
    """
    Случайный участник из глобального списка participants.
    """
    return db.query(models.Participant).order_by(func.random()).first()


def log_winner(
    db: Session,
    raffle_id: int,
    wallet: str,
    amount_lamports: int,
    tx_signature: str | None,
) -> models.RaffleWinner:
    winner = models.RaffleWinner(
        raffle_id=raffle_id,
        wallet=wallet,
        amount_lamports=amount_lamports,
        tx_signature=tx_signature,
    )
    db.add(winner)
    db.commit()
    db.refresh(winner)
    return winner
