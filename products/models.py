from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.cache import cache
from utils.images import process_image, PRODUCT_IMAGE_MAX, CATEGORY_IMAGE_MAX


class Category(models.Model):
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    image = models.ImageField('Изображение', upload_to='categories/', blank=True)
    description = models.TextField('Описание', blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.image and hasattr(self.image, 'file'):
            try:
                path, content = process_image(self.image, 'categories/', max_size=CATEGORY_IMAGE_MAX)
                self.image.save(path, content, save=False)
            except (ValueError, Exception):
                pass
        super().save(*args, **kwargs)
        cache.delete('nav_sections')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('nav_sections')


class Size(models.Model):
    name = models.CharField('Размер', max_length=10)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Размер'
        verbose_name_plural = 'Размеры'
        ordering = ['order']

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField('Цвет', max_length=50)
    hex_code = models.CharField('HEX код', max_length=7, default='#000000')

    class Meta:
        verbose_name = 'Цвет'
        verbose_name_plural = 'Цвета'

    def __str__(self):
        return self.name


class Product(models.Model):
    SECTION_WOMEN  = 'women'
    SECTION_MEN    = 'men'
    SECTION_KIDS   = 'kids'
    SECTION_UNISEX = 'unisex'
    SECTION_CHOICES = [
        (SECTION_WOMEN,  'Женская'),
        (SECTION_MEN,    'Мужская'),
        (SECTION_KIDS,   'Детская'),
        (SECTION_UNISEX, 'Унисекс'),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='products'
    )
    section = models.CharField(
        'Раздел', max_length=10,
        choices=SECTION_CHOICES, default=SECTION_UNISEX,
        db_index=True
    )
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField('Описание')
    composition = models.CharField('Состав', max_length=200, blank=True,
                                   help_text='Например: 80% хлопок, 20% полиэстер')
    care_instructions = models.TextField('Уход', blank=True)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    sale_price = models.DecimalField('Цена со скидкой', max_digits=12, decimal_places=2,
                                     null=True, blank=True)
    is_featured = models.BooleanField('Рекомендуемый', default=False, db_index=True)
    is_new = models.BooleanField('Новинка', default=True, db_index=True)
    is_active = models.BooleanField('Активен', default=True, db_index=True)
    meta_title = models.CharField('Meta заголовок', max_length=200, blank=True)
    meta_description = models.TextField('Meta описание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.price

    @property
    def discount_percent(self):
        if self.sale_price:
            return int((1 - self.sale_price / self.price) * 100)
        return 0

    @property
    def primary_image(self):
        # Uses prefetch cache when prefetch_related('images') is set on queryset.
        # Falls back to DB queries only when accessed without prefetch (e.g. detail page).
        first = primary = None
        for img in self.images.all():
            if first is None:
                first = img
            if img.is_primary:
                primary = img
                break
        return primary or first

    @property
    def avg_rating(self):
        # Uses 'approved_reviews' prefetch attr if available, otherwise hits DB.
        reviews = getattr(self, 'approved_reviews', None)
        if reviews is None:
            reviews = list(self.reviews.filter(is_approved=True))
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def reviews_count(self):
        reviews = getattr(self, 'approved_reviews', None)
        if reviews is None:
            return self.reviews.filter(is_approved=True).count()
        return len(reviews)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Изображение', upload_to='products/')
    color = models.ForeignKey(
        Color, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='images', verbose_name='Цвет фото'
    )
    alt_text = models.CharField('Alt текст', max_length=200, blank=True)
    is_primary = models.BooleanField('Главное', default=False)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'
        ordering = ['-is_primary', 'order']

    def __str__(self):
        return f'{self.product.name} - #{self.order}'

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            # Delete old image if updating
            if self.pk:
                try:
                    old = ProductImage.objects.get(pk=self.pk)
                    if old.image and old.image.name != self.image.name:
                        old.image.delete(save=False)
                except ProductImage.DoesNotExist:
                    pass
            try:
                path, content = process_image(self.image, 'products/', max_size=PRODUCT_IMAGE_MAX)
                self.image.save(path, content, save=False)
            except (ValueError, Exception):
                pass
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField('Остаток', default=0, db_index=True)
    sku = models.CharField('Артикул', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'
        unique_together = [('product', 'size', 'color')]

    def __str__(self):
        return f'{self.product.name} / {self.size} / {self.color}'

    @property
    def in_stock(self):
        return self.stock > 0


class Review(models.Model):
    RATING_CHOICES = [(i, '★' * i) for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField('Оценка', choices=RATING_CHOICES)
    title = models.CharField('Заголовок', max_length=200, blank=True)
    comment = models.TextField('Отзыв')
    is_approved = models.BooleanField('Одобрен', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = [('product', 'user')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.product} ({self.rating}★)'


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = [('user', 'product')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} ♥ {self.product}'
