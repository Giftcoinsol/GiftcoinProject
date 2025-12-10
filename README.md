<p align="center">
  <img src="app/static/img/logo.png" alt="Gift logo" width="160">
</p>

<h1 align="center">GIFT$ – Automated Giveaways on Solana</h1>

GIFT$ is a Solana meme token where a portion of **creator fees from trading is redistributed back to the community**.

Every time someone trades $GIFT, fees accumulate. A background worker periodically:

- collects creator fees,
- keeps a small reserve for gas,
- sends **70% to a random participant**,  
- sends **30% to the project owner** for development and operational costs.

You submit your wallet once — and you remain in all future giveaways automatically.

---

## 💡 How $GIFT Works

Whenever $GIFT is traded:

1. **Creator fees accumulate** on the token's creator wallet.
2. The backend worker integrates with **Pump.fun / PumpPortal** to:
   - collect the fees,
   - check the current balance,
   - keep a small **reserve (`RESERVE_SOL`)**,
   - split the remaining balance:
     - **70% → a random participant**,
     - **30% → the owner wallet**.
3. Payouts:
   - are sent on-chain in **SOL**,
   - include a real transaction signature,
   - are saved in the database,
   - appear on the website in the **Latest winners** feed.

No manual triggers. No admin decisions.  
**Giveaways run automatically and consistently in the background.**

---

## 🎟 How to Join the Giveaway

1. Get a Solana wallet  
   (Phantom, Solflare, Backpack, etc.)

2. Go to the $GIFT website and:
   - enter your **Solana address**,
   - complete the captcha,
   - press **Join giveaway**.

3. After that:
   - you are added to the global participants list,
   - you automatically participate in every future giveaway,
   - no need to resubmit your wallet ever again.

> You don’t have to trade or hold $GIFT to join the raffle —  
> but trading volume is what actually fills the reward pool.

---

## 🤝 Why You Can Trust the System

Not asking you to “just trust us” — here is what makes the setup reliable:

### ✅ 1. All payouts are fully on-chain  
- Winners receive SOL directly on the Solana blockchain.  
- Every payout has a **tx signature** visible in Solscan.  
- The website shows these signatures publicly, so anyone can verify payouts.

### ✅ 2. Open source backend  
The entire backend logic is here in this repository:

- how winners are chosen,
- the exact **70% / 30%** split,
- PumpPortal integration,
- wallet validation,
- raffle worker logic.

You can inspect, audit, or even self-host it if you want.

### ✅ 3. Transparent payout rules  
The giveaway split is simple and fixed:

- **70%** → random participant  
- **30%** → project owner  
- small reserve kept for fees

These numbers are explicitly defined in the worker code — nothing hidden.

### ✅ 4. No private keys from users  
You only submit a **public Solana wallet address**.  
We never request:
- private keys  
- seed phrases  
- secret keys  

All signing happens only with the creator wallet’s private key stored server-side.

---

## 🛠 Under the Hood (for devs & auditors)

**Language:** Python 3.12  
**Backend:** FastAPI + Uvicorn  
**Database:** PostgreSQL (SQLite supported for development)  
**ORM:** SQLAlchemy  
**Solana libraries:** `solana-py` + `solders`  

**Pump.fun / PumpPortal integration:**
- Lightning API (`/api/trade`)
- Local `trade-local` mode:
  - request serialized transaction
  - sign with `CREATOR_PRIVATE_KEY_BASE58`
  - broadcast through `SOLANA_RPC_URL`

**Raffle Worker Logic:**
- runs every N minutes,
- collects creator fees,
- keeps reserve,
- splits balance 70/30,
- selects a random participant,
- sends SOL on-chain,
- logs results in `raffle_winners`.

**Frontend:**
- Jinja2 templates  
- static HTML/CSS/JS  
- join form with captcha  
- scrolling “Latest winners” feed with Solscan links  


---

## 📎 Links

- X (Twitter): https://x.com/solanagiftcoin  
- GitHub: https://github.com/Giftcoinsol/GiftcoinProject  
- Our website: https://giftcoinsol.online