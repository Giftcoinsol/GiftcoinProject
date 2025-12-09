// ===== Join form (with optional reCAPTCHA) =====

const joinForm = document.getElementById("join-form");
const walletInput = document.getElementById("wallet-input");
const joinButton = document.getElementById("join-button");
const joinMessage = document.getElementById("join-message");

if (joinForm) {
  joinForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const wallet = walletInput.value.trim();
    if (!wallet) {
      setJoinMessage("Please enter your wallet address.", false);
      return;
    }

    // reCAPTCHA (если скрипт подключен и виджет есть)
    let recaptchaToken = null;
    if (window.grecaptcha) {
      recaptchaToken = grecaptcha.getResponse();
      if (!recaptchaToken) {
        setJoinMessage("Please complete the captcha.", false);
        return;
      }
    }

    joinButton.disabled = true;
    const prevText = joinButton.textContent;
    joinButton.textContent = "Submitting...";

    try {
      const payload = { wallet };
      if (recaptchaToken) {
        payload.recaptcha_token = recaptchaToken;
      }

      const resp = await fetch("/api/participants/join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        const detail = data?.detail || "Server error.";
        setJoinMessage(detail, false);
      } else {
        setJoinMessage(data.message || "Success.", true);
        // очищаем поле
        walletInput.value = "";
        // сбрасываем капчу
        if (window.grecaptcha) {
          grecaptcha.reset();
        }
      }
    } catch (err) {
      console.error(err);
      setJoinMessage("Failed to send request. Please try again later.", false);
    } finally {
      joinButton.disabled = false;
      joinButton.textContent = prevText;
    }
  });
}

function setJoinMessage(text, isOk) {
  if (!joinMessage) return;
  joinMessage.textContent = text;
  joinMessage.classList.remove("ok", "error");
  joinMessage.classList.add(isOk ? "ok" : "error");
}

// ===== Winners list (show txid + amount) =====

const winnersListEl = document.getElementById("winners-list");
// Используем Set, чтобы не дублировать уже показанные победы
let lastSeenKeys = new Set();

async function fetchLatestWinners() {
  if (!winnersListEl) return;

  try {
    const resp = await fetch("/api/winners/latest?limit=50");
    if (!resp.ok) return;

    const data = await resp.json();

    data.forEach((winner) => {
      const key = winner.tx_signature || `${winner.wallet}-${winner.amount_sol}`;
      if (lastSeenKeys.has(key)) return;
      lastSeenKeys.add(key);
      addWinnerRow(winner);
    });

    // Чтобы Set не разрастался бесконечно
    if (lastSeenKeys.size > 200) {
      lastSeenKeys = new Set(Array.from(lastSeenKeys).slice(-100));
    }
  } catch (err) {
    console.warn("Failed to fetch winners:", err);
  }
}

function addWinnerRow(winner) {
  if (!winnersListEl) return;

  const li = document.createElement("li");
  li.className = "winner-row";

  const amount = (winner.amount_sol || 0).toFixed(4);
  const hasTx = !!winner.tx_signature;

  const txText = hasTx ? winner.tx_signature : "tx pending";
  const txUrl = hasTx
    ? `https://solscan.io/tx/${winner.tx_signature}`
    : null;

  const txHtml = hasTx
    ? `<a href="${txUrl}" target="_blank" rel="noopener noreferrer" class="winner-tx-link">${txText}</a>`
    : `<span class="winner-tx-pending">${txText}</span>`;

  li.innerHTML = `
    <span class="winner-row-tx">${txHtml}</span>
    <span class="winner-row-amount">${amount} SOL</span>
  `;

  // Добавляем в начало списка
  if (winnersListEl.firstChild) {
    winnersListEl.insertBefore(li, winnersListEl.firstChild);
  } else {
    winnersListEl.appendChild(li);
  }

  // Ограничиваем длину списка
  const maxRows = 50;
  while (winnersListEl.children.length > maxRows) {
    winnersListEl.removeChild(winnersListEl.lastChild);
  }
}

// Первичная загрузка и обновление каждые 10 секунд
if (winnersListEl) {
  fetchLatestWinners();
  setInterval(fetchLatestWinners, 10000);
}
