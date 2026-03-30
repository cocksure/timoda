from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from utils.images import process_image, AVATAR_MAX


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField('Телефон', max_length=20, blank=True, unique=True, null=True)
    phone_verified = models.BooleanField('Телефон подтверждён', default=False)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    telegram_id = models.BigIntegerField('Telegram ID', null=True, blank=True, unique=True)
    telegram_username = models.CharField('Telegram username', max_length=100, blank=True)
    language = models.CharField('Язык', max_length=5, default='ru', choices=[
        ('ru', 'Русский'), ('uz', "O'zbek"), ('en', 'English'),
    ])
    avatar = models.ImageField('Фото', upload_to='avatars/', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email

    def get_full_name(self):
        name = f'{self.first_name} {self.last_name}'.strip()
        return name or self.email

    def save(self, *args, **kwargs):
        if self.avatar and hasattr(self.avatar, 'file'):
            try:
                path, content = process_image(self.avatar, 'avatars/', max_size=AVATAR_MAX)
                self.avatar.save(path, content, save=False)
            except (ValueError, Exception):
                pass
        # Set empty phone to None to avoid unique constraint issues
        if self.phone == '':
            self.phone = None
        super().save(*args, **kwargs)


class PhoneOTP(models.Model):
    """One-time password for phone verification."""
    phone = models.CharField('Телефон', max_length=20)
    code = models.CharField('Код', max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'OTP'
        verbose_name_plural = 'OTP коды'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} — {self.code}'

    @classmethod
    def create_for_phone(cls, phone: str, expiry_minutes: int = 5):
        from services.sms import generate_otp
        # Invalidate previous OTPs for this phone
        cls.objects.filter(phone=phone, is_used=False).update(is_used=True)
        code = generate_otp()
        return cls.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
        )

    @property
    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() < self.expires_at

    def verify(self, code: str) -> bool:
        from django.conf import settings
        self.attempts += 1
        self.save(update_fields=['attempts'])
        if self.attempts > getattr(settings, 'OTP_MAX_ATTEMPTS', 3):
            return False
        if self.is_valid and self.code == code:
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True
        return False


class Address(models.Model):
    TYPE_CHOICES = [
        ('shipping', 'Доставка'),
        ('billing', 'Оплата'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    type = models.CharField('Тип', max_length=10, choices=TYPE_CHOICES, default='shipping')
    full_name = models.CharField('ФИО', max_length=100)
    phone = models.CharField('Телефон', max_length=20)
    address_line1 = models.CharField('Адрес', max_length=255)
    address_line2 = models.CharField('Адрес 2', max_length=255, blank=True)
    city = models.CharField('Город', max_length=100)
    region = models.CharField('Регион', max_length=100, blank=True)
    postal_code = models.CharField('Индекс', max_length=20, blank=True)
    country = models.CharField('Страна', max_length=100, default='Узбекистан')
    is_default = models.BooleanField('По умолчанию', default=False)

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'

    def __str__(self):
        return f'{self.full_name}, {self.city}'

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(
                user=self.user, type=self.type, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)