import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./raffle.db")

    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    CREATOR_PRIVATE_KEY_BASE58: str = os.getenv("CREATOR_PRIVATE_KEY_BASE58", "")
    OWNER_WALLET: str = os.getenv("OWNER_WALLET", "")

    PUMPPORTAL_API_KEY: str = os.getenv("PUMPPORTAL_API_KEY", "")
    PUMP_POOL: str = os.getenv("PUMP_POOL", "pump")
    TOKEN_MINT: str | None = os.getenv("TOKEN_MINT") or None

    RECAPTCHA_SITE_KEY: str | None = os.getenv("RECAPTCHA_SITE_KEY") or None
    RECAPTCHA_SECRET: str | None = os.getenv("RECAPTCHA_SECRET") or None

    ACTIVE_RAFFLE_ID: int = int(os.getenv("ACTIVE_RAFFLE_ID", "1"))


settings = Settings()
