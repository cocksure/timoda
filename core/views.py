from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from .models import Banner, Subscriber
from products.models import Product, Category

HOME_CACHE_KEY = 'home_page_data'
HOME_CACHE_TTL = 60 * 15  # 15 минут


def home(request):
    ctx = cache.get(HOME_CACHE_KEY)
    if ctx is None:
        ctx = {
            'banners': list(Banner.objects.filter(is_active=True)),
            'featured': list(Product.objects.filter(is_active=True, is_featured=True).prefetch_related('images')[:8]),
            'new_arrivals': list(Product.objects.filter(is_active=True, is_new=True).prefetch_related('images')[:8]),
            'categories': list(Category.objects.filter(is_active=True, parent=None)[:6]),
            'sale_products': list(Product.objects.filter(is_active=True, sale_price__isnull=False).prefetch_related('images')[:4]),
        }
        cache.set(HOME_CACHE_KEY, ctx, HOME_CACHE_TTL)
    return render(request, 'core/home.html', ctx)


def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            _, created = Subscriber.objects.get_or_create(email=email)
            if created:
                messages.success(request, 'Спасибо! Вы успешно подписались.')
            else:
                messages.info(request, 'Вы уже подписаны на рассылку.')
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))