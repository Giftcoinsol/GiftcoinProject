

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import requests
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig
from solders.commitment_config import CommitmentLevel

from ..config import settings

logger = logging.getLogger(__name__)

PUMP_LIGHTNING_URL = "https://pumpportal.fun/api/trade"
PUMP_LOCAL_URL = "https://pumpportal.fun/api/trade-local"


def _collect_via_lightning() -> Optional[str]:
    api_key = settings.PUMPPORTAL_API_KEY
    if not api_key:
        logger.warning("collect_via_lightning called but PUMPPORTAL_API_KEY is empty")
        return None

    data: dict[str, object] = {
        "action": "collectCreatorFee",
        "priorityFee": 0.000001,
        "pool": settings.PUMP_POOL or "pump",
    }
    if settings.TOKEN_MINT:
        data["mint"] = settings.TOKEN_MINT

    resp = requests.post(
        f"{PUMP_LIGHTNING_URL}?api-key={api_key}",
        data=data,
        timeout=15,
    )
    resp.raise_for_status()
    j = resp.json()
    logger.info("PumpPortal lightning collectCreatorFee response: %s", j)

    sig = j.get("signature") or j.get("txSignature") or j.get("result")
    return sig


def _collect_via_local() -> Optional[str]:
    priv_b58 = settings.CREATOR_PRIVATE_KEY_BASE58
    if not priv_b58:
        logger.warning("collect_via_local called but CREATOR_PRIVATE_KEY_BASE58 is empty")
        return None

    kp = Keypair.from_base58_string(priv_b58)
    public_key = str(kp.pubkey())

    data: dict[str, object] = {
        "publicKey": public_key,
        "action": "collectCreatorFee",
        "pool": settings.PUMP_POOL or "pump",
    }
    if settings.TOKEN_MINT:
        data["mint"] = settings.TOKEN_MINT

    resp = requests.post(PUMP_LOCAL_URL, data=data, timeout=15)
    resp.raise_for_status()
    raw_tx_bytes = resp.content

    vtx = VersionedTransaction(
        VersionedTransaction.from_bytes(raw_tx_bytes).message,
        [kp],
    )

    commitment = CommitmentLevel.Confirmed
    config = RpcSendTransactionConfig(preflight_commitment=commitment)
    payload = SendVersionedTransaction(vtx, config).to_json()
    headers = {"Content-Type": "application/json"}

    r = requests.post(
        settings.SOLANA_RPC_URL,
        headers=headers,
        data=payload,
        timeout=30,
    )
    r.raise_for_status()
    out = r.json()
    sig = out.get("result")
    logger.info("Sent collectCreatorFee via local RPC: %s", out)
    return sig


def _collect_creator_fee_blocking() -> Optional[str]:
    try:
        if settings.PUMPPORTAL_API_KEY:
            logger.info("Using PumpPortal LIGHTNING collectCreatorFee")
            return _collect_via_lightning()
        else:
            logger.info("Using PumpPortal LOCAL trade-local collectCreatorFee")
            return _collect_via_local()
    except Exception as e:
        logger.error("Error while collecting creator fee: %s", e, exc_info=True)
        return None


async def collect_creator_fee() -> Optional[str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _collect_creator_fee_blocking)
