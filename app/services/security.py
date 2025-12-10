import httpx
from app.config import settings


async def verify_captcha(captcha_token: str) -> bool:
    if not settings.RECAPTCHA_SECRET:
        return True

    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": settings.RECAPTCHA_SECRET,
        "response": captcha_token,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data, timeout=5)
    j = resp.json()
    return bool(j.get("success"))
