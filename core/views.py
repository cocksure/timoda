from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Prefetch
from .models import Banner, Subscriber
from products.models import Product, Category, Review

HOME_CACHE_KEY = 'home_page_data'
HOME_CACHE_TTL = 60 * 15  # 15 минут


def _product_qs(filters, limit):
    """Shared queryset helper — images + variants + approved_reviews prefetched."""
    approved = Prefetch('reviews', queryset=Review.objects.filter(is_approved=True), to_attr='approved_reviews')
    return list(
        Product.objects.filter(is_active=True, **filters)
        .select_related('category')
        .prefetch_related('images', 'variants', approved)[:limit]
    )


def home(request):
    ctx = cache.get(HOME_CACHE_KEY)
    if ctx is None:
        ctx = {
            'banners':      list(Banner.objects.filter(is_active=True)),
            'featured':     _product_qs({'is_featured': True}, 8),
            'new_arrivals': _product_qs({'is_new': True}, 8),
            'sale_products':_product_qs({'sale_price__isnull': False}, 12),
            'categories':   list(Category.objects.filter(is_active=True, parent=None)[:6]),
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