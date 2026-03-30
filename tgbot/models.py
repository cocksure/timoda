import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class LoginToken(models.Model):
    """One-time token for auto-login from Telegram bot."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Токен входа'
        verbose_name_plural = 'Токены входа'

    @classmethod
    def create_for_user(cls, user):
        # Invalidate old tokens
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
        )

    @property
    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at) < timedelta(minutes=30)

    def get_url(self):
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f'{site_url}/telegram/auto-login/{self.token}/'