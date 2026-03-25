"""
eskiz.uz SMS Gateway service (my.eskiz.uz API)
"""
import random
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

ESKIZ_BASE_URL = "https://my.eskiz.uz/api"
ESKIZ_TOKEN_CACHE_KEY = "eskiz_token"
ESKIZ_TOKEN_TTL = 60 * 60 * 23  # refresh every 23 hours


def _get_token() -> str:
    """Get or refresh eskiz.uz token (cached)."""
    token = cache.get(ESKIZ_TOKEN_CACHE_KEY)
    if token:
        return token

    resp = requests.post(
        f"{ESKIZ_BASE_URL}/auth/login",
        data={
            "email": settings.ESKIZ_EMAIL,
            "password": settings.ESKIZ_PASSWORD,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    cache.set(ESKIZ_TOKEN_CACHE_KEY, token, ESKIZ_TOKEN_TTL)
    return token


def generate_otp(length: int = 6) -> str:
    return str(random.randint(10 ** (length - 1), 10**length - 1))


def send_sms(phone: str, message: str) -> dict:
    """
    Send SMS via my.eskiz.uz.
    Phone is normalized to 9-digit local format (without 998).
    """
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if phone.startswith("998"):
        phone = phone[3:]
    phone = phone.lstrip("0")

    token = _get_token()
    resp = requests.post(
        f"{ESKIZ_BASE_URL}/send-sms/single",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sending": "server1",
            "phone": phone,
            "text": message,
            "nik_id": getattr(settings, "ESKIZ_SENDER", "4546"),
            "count": 0,
            "client_id": getattr(settings, "ESKIZ_CLIENT_ID", ""),
        },
        timeout=10,
    )
    result = resp.json()
    if result.get("status") != "success":
        logger.error("eskiz.uz error: %s", result)
    return result


def send_otp(phone: str, code: str) -> bool:
    """Send OTP verification code. Returns True on success."""
    message = f"TIMODA: Ваш код подтверждения: {code}. Действителен 5 минут."
    try:
        result = send_sms(phone, message)
        return result.get("status") == "success"
    except Exception as e:
        logger.exception("Failed to send OTP to %s: %s", phone, e)
        return False