from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import VersionedTransaction
from solders.message import MessageV0

from ..config import settings

LAMPORTS_PER_SOL = 1_000_000_000


if not settings.SOLANA_RPC_URL:
    raise RuntimeError("SOLANA_RPC_URL is not set in .env")

if not settings.CREATOR_PRIVATE_KEY_BASE58:
    raise RuntimeError("CREATOR_PRIVATE_KEY_BASE58 is not set in .env")

if not settings.OWNER_WALLET:
    raise RuntimeError("OWNER_WALLET is not set in .env")


CREATOR_KEYPAIR: Keypair = Keypair.from_base58_string(
    settings.CREATOR_PRIVATE_KEY_BASE58
)
CREATOR_PUBKEY: Pubkey = CREATOR_KEYPAIR.pubkey()
OWNER_PUBKEY: Pubkey = Pubkey.from_string(settings.OWNER_WALLET)


async def get_creator_balance_lamports() -> int:
    async with AsyncClient(settings.SOLANA_RPC_URL) as client:
        resp = await client.get_balance(CREATOR_PUBKEY)
        return resp.value


async def send_sol_from_creator(to_address: str, lamports: int) -> str:
    to_pubkey = Pubkey.from_string(to_address)

    async with AsyncClient(settings.SOLANA_RPC_URL) as client:
        latest_blockhash = await client.get_latest_blockhash()
        blockhash = latest_blockhash.value.blockhash

        ix = transfer(
            TransferParams(
                from_pubkey=CREATOR_PUBKEY,
                to_pubkey=to_pubkey,
                lamports=lamports,
            )
        )

        msg = MessageV0.try_compile(
            payer=CREATOR_PUBKEY,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )

        tx = VersionedTransaction(msg, [CREATOR_KEYPAIR])

        resp = await client.send_transaction(tx)
        sig = resp.value

        print(
            f"[solana_client] Sent {lamports} lamports "
            f"from {CREATOR_PUBKEY} to {to_pubkey}, tx={sig}"
        )
        return str(sig)
