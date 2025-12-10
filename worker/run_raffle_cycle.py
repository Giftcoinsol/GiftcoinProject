import asyncio
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services import pumpportal, solana_client, raffle_logic


RESERVE_SOL = 0.002

GIFT_NUMERATOR = 7
GIFT_DENOMINATOR = 10

RAFFLE_INTERVAL_SECONDS = 5 * 60


async def run_raffle_once() -> None:
    db: Session = SessionLocal()
    try:
        raffle = raffle_logic.get_active_raffle(
            db=db, raffle_id=settings.ACTIVE_RAFFLE_ID
        )
        if not raffle:
            print(f"[worker] No active raffle with id {settings.ACTIVE_RAFFLE_ID}")
            return

        is_devnet = "devnet" in settings.SOLANA_RPC_URL.lower()

        sig: str | None = None

        if is_devnet:
            print(
                "[worker] Devnet mode detected – skipping PumpPortal collectCreatorFee "
                "(using balance-based distribution for tests)"
            )
        else:
            try:
                print(
                    "[worker] Collecting creator fees via PumpPortal (lightning or local)..."
                )
                sig = await pumpportal.collect_creator_fee()

                if sig:
                    print(f"[worker] collectCreatorFee tx signature: {sig}")
                else:
                    print(
                        "[worker] collectCreatorFee completed (no tx signature returned, "
                        "maybe no fees yet)"
                    )

                await asyncio.sleep(10)
            except Exception as e:
                print("[worker] Error calling PumpPortal collectCreatorFee:", e)
                return


        if is_devnet:
            balance = await solana_client.get_creator_balance_lamports()
            print(f"[worker] [devnet] Creator balance: {balance} lamports")

            reserve_lamports = int(
                RESERVE_SOL * solana_client.LAMPORTS_PER_SOL
            )
            distributable = balance - reserve_lamports
            if distributable <= 0:
                print(
                    "[worker] [devnet] Nothing to distribute "
                    "(balance too low after reserve)"
                )
                return
        else:
            if not sig:
                print(
                    "[worker] [mainnet] No tx signature from PumpPortal – "
                    "cannot safely compute creator fees. Skipping round."
                )
                return

            try:
                fee_delta = await solana_client.get_creator_fee_delta_from_tx(sig)
            except Exception as e:
                print(
                    "[worker] [mainnet] Failed to compute fee delta from tx:", e
                )
                return

            if fee_delta <= 0:
                print(
                    "[worker] [mainnet] Fee delta <= 0 – nothing to distribute "
                    "(maybe only tx fee, no creator fees)."
                )
                return

            distributable = fee_delta


        raffle_part = distributable * GIFT_NUMERATOR // GIFT_DENOMINATOR
        owner_part = distributable - raffle_part

        print(
            "[worker] Distributable:", distributable,
            "owner_part:", owner_part,
            "raffle_part:", raffle_part,
        )

        participant = raffle_logic.get_random_participant(db=db)
        if not participant:
            print("[worker] No participants in global list")
            return

        print(f"[worker] Selected winner wallet: {participant.wallet}")


        try:
            owner_sig = await solana_client.send_sol_from_creator(
                settings.OWNER_WALLET,
                owner_part,
            )
            print("[worker] Owner tx:", owner_sig)
        except Exception as e:
            print("[worker] Error sending SOL to owner:", e)
            return


        try:
            winner_sig = await solana_client.send_sol_from_creator(
                participant.wallet,
                raffle_part,
            )
            print("[worker] Winner tx:", winner_sig)
        except Exception as e:
            print("[worker] Error sending SOL to winner:", e)
            winner_sig = None


        raffle_logic.log_winner(
            db=db,
            raffle_id=raffle.id,
            wallet=participant.wallet,
            amount_lamports=raffle_part,
            tx_signature=winner_sig,
        )
        print("[worker] Raffle winner logged in DB")

    finally:
        db.close()


async def main_loop() -> None:
    print("[worker] Starting raffle loop...")
    while True:
        try:
            await run_raffle_once()
        except Exception as e:
            print("[worker] Unexpected error in run_raffle_once:", repr(e))

        print(f"[worker] Sleeping for {RAFFLE_INTERVAL_SECONDS} seconds...")
        await asyncio.sleep(RAFFLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main_loop())
