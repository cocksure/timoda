"""
Run: python manage.py shell < create_demo_data.py
Creates demo data: superuser, categories, sizes, colors, products
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Category, Size, Color, Product, ProductVariant
from core.models import Banner

User = get_user_model()

# Superuser
if not User.objects.filter(email='admin@timda.uz').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@timoda.uz',
        password='admin123',
        first_name='Admin',
        last_name='TIMODA'
    )
    print('Superuser created: admin@timoda.uz / admin123')

# Sizes
sizes_data = [('XS', 0), ('S', 1), ('M', 2), ('L', 3), ('XL', 4), ('XXL', 5)]
for name, order in sizes_data:
    Size.objects.get_or_create(name=name, defaults={'order': order})

# Colors
colors_data = [
    ('Молочный', '#F5F0EB'),
    ('Бежевый', '#C4A882'),
    ('Коричневый', '#8B6914'),
    ('Серый', '#9E9E9E'),
    ('Чёрный', '#1A1A1A'),
    ('Белый', '#FFFFFF'),
    ('Терракотовый', '#C0614E'),
    ('Оливковый', '#6B7040'),
]
for name, hex_code in colors_data:
    Color.objects.get_or_create(name=name, defaults={'hex_code': hex_code})

# Categories
categories_data = [
    ('Свитеры', 'svitery'),
    ('Кардиганы', 'kardigany'),
    ('Платья', 'platya'),
    ('Джемперы', 'djempery'),
    ('Жилеты', 'jilet'),
    ('Аксессуары', 'aksessuary'),
]
for name, slug in categories_data:
    Category.objects.get_or_create(slug=slug, defaults={'name': name})

# Sample products
products_data = [
    {
        'name': 'Оверсайз свитер «Уют»',
        'slug': 'oversajz-sviter-uyut',
        'description': 'Мягкий оверсайз свитер из премиального хлопка с добавлением кашемира. Идеален для уютных вечеров и повседневного стиля.',
        'composition': '70% хлопок, 20% кашемир, 10% полиамид',
        'care_instructions': 'Ручная стирка при 30°C, не отжимать',
        'price': 185000,
        'is_featured': True,
        'is_new': True,
        'category_slug': 'svitery',
    },
    {
        'name': 'Кардиган «Осень»',
        'slug': 'kardigan-osen',
        'description': 'Длинный кардиган на пуговицах с глубокими карманами. Универсальная вещь для прохладного сезона.',
        'composition': '60% шерсть мериноса, 40% акрил',
        'care_instructions': 'Сухая чистка',
        'price': 220000,
        'sale_price': 176000,
        'is_featured': True,
        'is_new': False,
        'category_slug': 'kardigany',
    },
    {
        'name': 'Трикотажное платье «Миди»',
        'slug': 'trikotajnoe-platie-midi',
        'description': 'Элегантное платье-миди из мягкого вязаного полотна. Приталенный силуэт подчёркивает фигуру.',
        'composition': '80% вискоза, 20% эластан',
        'care_instructions': 'Стирка при 30°C в деликатном режиме',
        'price': 265000,
        'is_featured': True,
        'is_new': True,
        'category_slug': 'platya',
    },
    {
        'name': 'Джемпер «Базовый»',
        'slug': 'djemper-bazoviy',
        'description': 'Классический джемпер с круглым вырезом. Основа любого гардероба.',
        'composition': '100% хлопок',
        'price': 145000,
        'is_new': True,
        'category_slug': 'djempery',
    },
    {
        'name': 'Свитер с косами «Нордик»',
        'slug': 'sviter-s-kosami-nordik',
        'description': 'Объёмный свитер с классическим норвежским узором «косы». Тёплый и стильный.',
        'composition': '50% шерсть, 50% акрил',
        'price': 198000,
        'sale_price': 158000,
        'is_new': False,
        'category_slug': 'svitery',
    },
]

size_m = Size.objects.get(name='M')
size_l = Size.objects.get(name='L')
color_beige = Color.objects.get(name='Бежевый')
color_black = Color.objects.get(name='Чёрный')

for i, data in enumerate(products_data):
    category = Category.objects.get(slug=data.pop('category_slug'))
    product, created = Product.objects.get_or_create(
        slug=data['slug'],
        defaults={**data, 'category': category}
    )
    if created:
        ProductVariant.objects.get_or_create(
            product=product, size=size_m, color=color_beige,
            defaults={'stock': 10, 'sku': f'KN-{i+1:03d}-M-BEI'}
        )
        ProductVariant.objects.get_or_create(
            product=product, size=size_l, color=color_black,
            defaults={'stock': 7, 'sku': f'KN-{i+1:03d}-L-BLK'}
        )
        print(f'Created product: {product.name}')

print('\nDemo data created successfully!')
print('Admin: admin@timoda.uz / admin123')