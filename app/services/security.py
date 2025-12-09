import httpx
from app.config import settings


async def verify_captcha(captcha_token: str) -> bool:
    """
    Проверка капчи.
    Если RECAPTCHA_SECRET не задан, капча считается всегда валидной.
    Здесь пример под Google reCAPTCHA.
    """
    if not settings.RECAPTCHA_SECRET:
        # капча выключена — пропускаем
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
