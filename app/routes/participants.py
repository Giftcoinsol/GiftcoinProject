from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from solders.pubkey import Pubkey

from app.deps import get_db, rate_limit_dep
from app import models
from app.config import settings

import requests

router = APIRouter(prefix="/api/participants", tags=["participants"])


class ParticipantJoinRequest(BaseModel):
    wallet: str
    recaptcha_token: str | None = None  # токен от reCAPTCHA (g-recaptcha-response)


class ParticipantJoinResponse(BaseModel):
    ok: bool
    message: str


def _validate_solana_wallet(addr: str) -> str:
    """
    Проверка, что строка — валидный Solana public key (base58, 32 байта).
    Возвращает нормализованную строку (без пробелов).
    Бросает HTTPException, если адрес невалидный.
    """
    cleaned = addr.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet address is required.",
        )

    try:
        _ = Pubkey.from_string(cleaned)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Solana wallet address.",
        )

    return cleaned


def _verify_recaptcha(token: str, remote_ip: str | None = None) -> bool:
    """
    Проверка Google reCAPTCHA v2.
    Если RECAPTCHA_SECRET не задан, считаем что капча выключена и всегда возвращаем True.
    """
    secret = settings.RECAPTCHA_SECRET
    if not secret:
        # капча выключена через настройки
        return True

    if not token:
        return False

    data = {
        "secret": secret,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        resp = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data,
            timeout=5,
        )
        resp.raise_for_status()
        out = resp.json()
        return bool(out.get("success"))
    except Exception:
        # если сервер капчи лёг — лучше не пропускать ботов
        return False


@router.post(
    "/join",
    response_model=ParticipantJoinResponse,
    dependencies=[Depends(rate_limit_dep)],
)
def join_participants(
    payload: ParticipantJoinRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # --- reCAPTCHA ---
    if settings.RECAPTCHA_SECRET:
        # капча включена → токен обязателен
        if not payload.recaptcha_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Captcha is required.",
            )

        client_ip = request.client.host if request.client else None
        ok = _verify_recaptcha(payload.recaptcha_token, client_ip)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Captcha verification failed.",
            )

    # --- Валидация кошелька ---
    wallet = _validate_solana_wallet(payload.wallet)

    # Уже есть такой участник?
    existing = db.query(models.Participant).filter_by(wallet=wallet).first()
    if existing:
        return ParticipantJoinResponse(
            ok=True,
            message="You are already in the participants list.",
        )

    participant = models.Participant(wallet=wallet)

    try:
        db.add(participant)
        db.commit()
        db.refresh(participant)
    except IntegrityError:
        # На случай гонки: второй параллельный INSERT того же кошелька
        db.rollback()
        return ParticipantJoinResponse(
            ok=True,
            message="You are already in the participants list.",
        )

    return ParticipantJoinResponse(
        ok=True,
        message="You have been successfully added to the participants list.",
    )
