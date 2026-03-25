from django.db import models
from orders.models import Order


class Payment(models.Model):
    PROVIDER_PAYME = 'payme'
    PROVIDER_CLICK = 'click'
    PROVIDER_CHOICES = [
        (PROVIDER_PAYME, 'Payme'),
        (PROVIDER_CLICK, 'Click'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_WAITING = 'waiting'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING,   'Ожидает'),
        (STATUS_WAITING,   'В обработке'),
        (STATUS_PAID,      'Оплачен'),
        (STATUS_CANCELLED, 'Отменён'),
        (STATUS_FAILED,    'Ошибка'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField('Провайдер', max_length=10, choices=PROVIDER_CHOICES)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Amount in tiyin (1 sum = 100 tiyin) — Payme uses tiyin, Click uses sum
    amount = models.BigIntegerField('Сумма (тийин)')

    # Provider-side transaction IDs
    provider_transaction_id = models.CharField('ID транзакции', max_length=100, blank=True)
    provider_time = models.BigIntegerField('Время (ms)', null=True, blank=True)

    # Raw webhook payloads for debugging
    request_data = models.JSONField('Данные запроса', default=dict, blank=True)
    response_data = models.JSONField('Данные ответа', default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_provider_display()} #{self.order.order_number} — {self.get_status_display()}'

    @property
    def amount_sum(self):
        """Amount in UZS sum (divide tiyin by 100)."""
        return self.amount / 100