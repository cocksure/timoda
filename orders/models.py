import uuid
from django.db import models
from django.conf import settings


def generate_order_number():
    return uuid.uuid4().hex[:10].upper()


class PickupPoint(models.Model):
    name = models.CharField('Название', max_length=200)
    address = models.CharField('Адрес', max_length=300)
    city = models.CharField('Город', max_length=100, default='Ташкент')
    working_hours = models.CharField('Часы работы', max_length=100, blank=True,
                                     help_text='Например: Пн–Пт 9:00–19:00')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Пункт выдачи'
        verbose_name_plural = 'Пункты выдачи'
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name} — {self.address}'


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Ожидает'),
        (STATUS_CONFIRMED, 'Подтверждён'),
        (STATUS_PROCESSING, 'В обработке'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_DELIVERED, 'Доставлен'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    DELIVERY_COURIER = 'courier'
    DELIVERY_PICKUP = 'pickup'
    DELIVERY_CHOICES = [
        (DELIVERY_COURIER, 'Доставка курьером'),
        (DELIVERY_PICKUP, 'Самовывоз из пункта выдачи'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    order_number = models.CharField('Номер заказа', max_length=20, unique=True, editable=False)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    delivery_method = models.CharField('Способ получения', max_length=20,
                                       choices=DELIVERY_CHOICES, default=DELIVERY_COURIER)
    pickup_point = models.ForeignKey(
        PickupPoint, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name='Пункт выдачи'
    )

    full_name = models.CharField('ФИО', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    shipping_address = models.TextField('Адрес доставки')
    city = models.CharField('Город', max_length=100)
    postal_code = models.CharField('Индекс', max_length=20, blank=True)
    country = models.CharField('Страна', max_length=100, default='Узбекистан')
    notes = models.TextField('Примечания', blank=True)
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)

    subtotal = models.DecimalField('Сумма', max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField('Доставка', max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField('Итого', max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.order_number}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)
        self._original_status = self.status


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(
        'products.ProductVariant', on_delete=models.SET_NULL, null=True
    )
    product_name = models.CharField('Товар', max_length=200)
    size_name = models.CharField('Размер', max_length=20)
    color_name = models.CharField('Цвет', max_length=50)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Позиция'
        verbose_name_plural = 'Позиции'

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    @property
    def total_price(self):
        return self.price * self.quantity

    @property
    def primary_image(self):
        if self.variant and self.variant.product_id:
            return self.variant.product.images.filter(is_primary=True).first() \
                   or self.variant.product.images.first()
        return None

    @property
    def product_slug(self):
        if self.variant and self.variant.product_id:
            return self.variant.product.slug
        return None
