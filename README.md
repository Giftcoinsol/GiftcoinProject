# Giftcoin – Giveaway Backend & Landing

Backend + simple landing page for automated giveaways of creator fees from the **$GIFTCOIN** token on Solana.

- Backend built with **FastAPI**
- Database: **PostgreSQL** (SQLite for local dev is also supported)
- Integration with **Pump.fun / PumpPortal**
- Automatic giveaway rounds every N minutes (worker)
- Landing page with join form and live winners feed

---

## 🚀 Tech Stack

- **Python 3.12**
- **FastAPI** + **Uvicorn**
- **SQLAlchemy**
- **PostgreSQL** / SQLite
- **solana-py** + **solders**
- **PumpPortal API** (Lightning + Local trade-local)
- **Jinja2** templates
- Static: HTML / CSS / JS


---

## 🔁 Giveaway Logic (High Level)

1. **Collect creator fees**
   - If `DEVNET=1` → fee collection is skipped (test mode).
   - If `DEVNET=0`:
     - If `PUMPPORTAL_API_KEY` is set → use **Lightning API**
     - If `PUMPPORTAL_API_KEY` is empty → use **trade-local**:
       - request serialized transaction from PumpPortal,
       - sign it with `CREATOR_PRIVATE_KEY_BASE58`,
       - send it to `SOLANA_RPC_URL`.

2. **Distribute funds**
   - Keep a small reserve `RESERVE_SOL` on the creator wallet for future fees.
   - Remaining balance is split into:
     - `owner_part` → `OWNER_WALLET` (e.g. 30%)
     - `raffle_part` → random participant (70%)

3. **Store winner in DB**
   - Winner is saved in `raffle_winners` with amount and tx signature.
   - Frontend uses `/api/winners/latest` to show the latest payouts.

---

## 🎨 Frontend Overview

The landing page (`index.html` + `main.css` + `main.js`) is a minimalist, responsive layout:

- Fixed top bar with:
  - token logo on the left,
  - token mint address on the right.
- Centered content with:
  - title: `$GIFTCOIN giveaway`
  - short project description,
  - input field for Solana wallet,
  - **Join giveaway** button.
- Bottom footer with:
  - X (Twitter) icon,
  - GitHub icon.
- Scrollable “Latest winners” list:
  - `tx` link to Solscan,
  - shortened winner wallet,
  - payout amount in SOL.

---

## 🔐 Solana Wallet Validation

The backend strictly validates wallet input:

- must be a valid **base58** string,
- must successfully parse via `Pubkey.from_string(...)`,
- invalid wallets return `HTTP 400` with `"Invalid Solana wallet address"`,
- duplicates are not created (one wallet → one participant entry).

This prevents garbage strings from polluting the participants list.

---

## 📬 Project Links

- X (Twitter): https://x.com/solanagiftcoin  
- GitHub: https://github.com/Giftcoinsol/GiftcoinProject  

---

## 📄 License

MIT License
