from typing import Optional
import httpx

from ..config import settings


def verify_recaptcha(token: str, remote_ip: Optional[str] = None) -> bool:
    """
    Verify Google reCAPTCHA v3 token.
    If RECAPTCHA_SECRET is not set, captcha is treated as disabled (always True).
    """
    secret = settings.RECAPTCHA_SECRET
    if not secret:
        # Captcha disabled – always allow (useful for local dev)
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
        resp = httpx.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data,
            timeout=5.0,
        )
        resp.raise_for_status()
        j = resp.json()
    except Exception as e:
        print("[recaptcha] error:", e)
        return False

    success = j.get("success", False)
    score = j.get("score", 0.0)
    action = j.get("action", "")

    if not success:
        return False

    # Simple threshold for v3
    if score < 0.3:
        return False

    # We expect action="join" from front-end
    if action and action != "join":
        return False

    return True
