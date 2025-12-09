from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.deps import get_db
from app import models

router = APIRouter(prefix="/api/winners", tags=["winners"])


class WinnerOut(BaseModel):
    wallet: str
    amount_sol: float
    tx_signature: str | None


@router.get("/latest", response_model=list[WinnerOut])
def get_latest_winners(limit: int = 5, db: Session = Depends(get_db)):
    """
    Return latest raffle winners for front-end to display as live feed.
    """
    rows = (
        db.query(models.RaffleWinner)
        .order_by(models.RaffleWinner.created_at.desc())
        .limit(limit)
        .all()
    )

    result: list[WinnerOut] = []
    for w in rows:
        result.append(
            WinnerOut(
                wallet=w.wallet,
                amount_sol=w.amount_lamports / 1_000_000_000,
                tx_signature=w.tx_signature,
            )
        )

    return result
