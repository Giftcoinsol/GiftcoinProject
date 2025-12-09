import asyncio
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services import pumpportal, solana_client, raffle_logic

# Сколько SOL оставляем на кошельке создателя под комиссии
RESERVE_SOL = 0.002

# Какую долю distributable отдаём участникам (например, 70%)
GIFT_NUMERATOR = 7
GIFT_DENOMINATOR = 10

# Интервал между раффлами (в секундах)
RAFFLE_INTERVAL_SECONDS = 5 * 60  # 5 минут


async def run_raffle_once() -> None:
    """
    Один цикл розыгрыша:
      1. На mainnet: собираем creator fees через PumpPortal
         (внутри выбирается lightning или local).
      2. Смотрим баланс creator-кошелька.
      3. Оставляем резерв.
      4. Остальное делим: часть владельцу, часть победителю.
      5. Выбираем победителя из global participants.
      6. Отправляем SOL.
      7. Логируем победителя в БД.
    """
    db: Session = SessionLocal()
    try:
        # 1. Находим активный раффл по ID из .env
        raffle = raffle_logic.get_active_raffle(db=db, raffle_id=settings.ACTIVE_RAFFLE_ID)
        if not raffle:
            print(f"[worker] No active raffle with id {settings.ACTIVE_RAFFLE_ID}")
            return

        # 2. Определяем devnet / mainnet по RPC URL
        is_devnet = "devnet" in settings.SOLANA_RPC_URL.lower()

        if is_devnet:
            # На devnet не трогаем PumpPortal, просто работаем с тем, что уже есть на кошельке
            print("[worker] Devnet mode detected – skipping PumpPortal collectCreatorFee")
        else:
            # На mainnet ВСЕГДА вызываем наш универсальный collect_creator_fee:
            #   - если PUMPPORTAL_API_KEY есть -> lightning
            #   - если его нет -> local trade-local + подпись приватником
            try:
                print("[worker] Collecting creator fees via PumpPortal (lightning or local)...")
                sig = await pumpportal.collect_creator_fee()

                if sig:
                    print(f"[worker] collectCreatorFee tx signature: {sig}")
                else:
                    print("[worker] collectCreatorFee completed (no tx signature returned, maybe no fees yet)")

                # Немного подождём, чтобы транза дошла и баланс обновился
                await asyncio.sleep(10)
            except Exception as e:
                print("[worker] Error calling PumpPortal collectCreatorFee:", e)
                return

        # 3. Баланс creator-кошелька
        balance = await solana_client.get_creator_balance_lamports()
        print(f"[worker] Creator balance: {balance} lamports")

        reserve_lamports = int(RESERVE_SOL * solana_client.LAMPORTS_PER_SOL)
        distributable = balance - reserve_lamports
        if distributable <= 0:
            print("[worker] Nothing to distribute (balance too low after reserve)")
            return

        # 70% участнику, 30% владельцу (всё в целых лампортах)
        raffle_part = distributable * GIFT_NUMERATOR // GIFT_DENOMINATOR
        owner_part = distributable - raffle_part

        print(
            "[worker] Distributable:", distributable,
            "owner_part:", owner_part,
            "raffle_part:", raffle_part,
        )

        # 4. Выбираем случайного участника
        participant = raffle_logic.get_random_participant(db=db)
        if not participant:
            print("[worker] No participants in global list")
            return

        print(f"[worker] Selected winner wallet: {participant.wallet}")

        # 5. Отправляем владельцу
        try:
            owner_sig = await solana_client.send_sol_from_creator(
                settings.OWNER_WALLET,
                owner_part,
            )
            print("[worker] Owner tx:", owner_sig)
        except Exception as e:
            print("[worker] Error sending SOL to owner:", e)
            return

        # 6. Отправляем победителю
        try:
            winner_sig = await solana_client.send_sol_from_creator(
                participant.wallet,
                raffle_part,
            )
            print("[worker] Winner tx:", winner_sig)
        except Exception as e:
            print("[worker] Error sending SOL to winner:", e)
            winner_sig = None

        # 7. Логируем победителя
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
    """
    Бесконечный цикл: раз в RAFFLE_INTERVAL_SECONDS запускает run_raffle_once().
    Любая ошибка в одном цикле логируется и не ломает весь воркер.
    """
    print("[worker] Starting raffle loop...")
    while True:
        try:
            await run_raffle_once()
        except Exception as e:
            # чтобы одна ошибка не убивала весь вечный цикл
            print("[worker] Unexpected error in run_raffle_once:", repr(e))

        print(f"[worker] Sleeping for {RAFFLE_INTERVAL_SECONDS} seconds...")
        await asyncio.sleep(RAFFLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main_loop())
