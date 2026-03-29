from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.core.cache import cache
from .models import Product, Category, Review, ProductVariant, Favorite
from django import forms as django_forms

PRODUCT_CACHE_TTL = 60 * 15  # 15 минут


class ReviewForm(django_forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': django_forms.RadioSelect(),
            'comment': django_forms.Textarea(attrs={'rows': 4}),
        }


SECTION_LABELS = {
    'women': 'Женская', 'men': 'Мужская',
    'kids': 'Детская', 'unisex': 'Унисекс',
}


def product_list(request):
    approved_reviews_prefetch = Prefetch(
        'reviews',
        queryset=Review.objects.filter(is_approved=True),
        to_attr='approved_reviews'
    )
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        'images', 'variants', approved_reviews_prefetch,
    )
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')

    section = request.GET.get('section', '').strip()
    category_slug = request.GET.get('category')
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '-created_at')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    is_sale = request.GET.get('sale')
    is_new = request.GET.get('is_new')
    is_featured = request.GET.get('is_featured')

    selected_section_label = ''
    if section and section in SECTION_LABELS:
        if section == 'unisex':
            products = products.filter(section='unisex')
        else:
            products = products.filter(section__in=[section, 'unisex'])
        selected_section_label = SECTION_LABELS[section]

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if is_sale:
        products = products.filter(sale_price__isnull=False)
    if is_new:
        products = products.filter(is_new=True)
    if is_featured:
        products = products.filter(is_featured=True)

    valid_sorts = {'-created_at', 'price', '-price', 'name'}
    if sort in valid_sorts:
        products = products.order_by(sort)

    paginator = Paginator(products, 24)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)

    is_htmx = request.headers.get('HX-Request')
    template = 'products/partials/product_grid.html' if is_htmx else 'products/list.html'

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, template, {
        'products': products_page,
        'page_obj': products_page,
        'categories': categories,
        'selected_category': selected_category,
        'section': section,
        'selected_section_label': selected_section_label,
        'query': q,
        'sort': sort,
        'favorite_ids': favorite_ids,
    })


def product_detail(request, slug):
    cache_key = f'product_detail_{slug}'
    ctx = cache.get(cache_key)

    if ctx is None:
        product = get_object_or_404(
            Product.objects.prefetch_related('images', 'variants__size', 'variants__color', 'reviews__user'),
            slug=slug, is_active=True
        )
        variants = product.variants.filter(stock__gt=0)
        sizes = sorted(set(v.size for v in product.variants.all()), key=lambda s: s.order)
        colors = list(set(v.color for v in product.variants.all()))
        reviews = list(product.reviews.all())
        related = list(Product.objects.filter(
            category=product.category, is_active=True
        ).exclude(pk=product.pk).prefetch_related('images')[:4])

        variant_map = {}
        stock_map = {}
        for v in product.variants.all():
            variant_map.setdefault(v.size_id, {})[v.color_id] = v.id
            stock_map[v.id] = v.stock

        color_image_map = {}
        all_images = []
        for img in product.images.all():
            all_images.append(img.image.url)
            if img.color_id:
                color_image_map.setdefault(str(img.color_id), []).append(img.image.url)

        ctx = {
            'product': product,
            'variants': list(variants),
            'sizes': sizes,
            'colors': colors,
            'reviews': reviews,
            'related': related,
            'variant_map': variant_map,
            'color_image_map': color_image_map,
            'all_images': all_images,
            'stock_map': stock_map,
        }
        cache.set(cache_key, ctx, PRODUCT_CACHE_TTL)

    # review_form и cart_variant_ids вне кэша — зависят от пользователя
    ctx['review_form'] = None
    if request.user.is_authenticated:
        if not ctx['product'].reviews.filter(user=request.user).exists():
            ctx['review_form'] = ReviewForm()

    from cart.cart import Cart
    cart = Cart(request)
    ctx['cart_variant_ids'] = list({item['variant'].id for item in cart})
    ctx['is_fav'] = (
        request.user.is_authenticated
        and Favorite.objects.filter(user=request.user, product=ctx['product']).exists()
    )

    return render(request, 'products/detail.html', ctx)


@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if product.reviews.filter(user=request.user).exists():
        messages.warning(request, 'Вы уже оставили отзыв на этот товар.')
        if request.headers.get('HX-Request'):
            return render(request, 'products/partials/review_thanks.html')
        return redirect('products:detail', slug=slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        cache.delete(f'product_detail_{slug}')
        if request.headers.get('HX-Request'):
            return render(request, 'products/partials/review_thanks.html')
        messages.success(request, 'Спасибо за отзыв!')

    return redirect('products:detail', slug=slug)


def quick_view(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related('images', 'variants__size', 'variants__color'),
        slug=slug, is_active=True
    )
    sizes = sorted(set(v.size for v in product.variants.all()), key=lambda s: s.order)
    colors = list(set(v.color for v in product.variants.all()))
    first_variant = product.variants.first()
    return render(request, 'products/partials/quick_view.html', {
        'product': product,
        'sizes': sizes,
        'colors': colors,
        'first_variant': first_variant,
    })


def search_suggest(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    products = Product.objects.filter(
        is_active=True
    ).filter(
        Q(name__icontains=q) | Q(category__name__icontains=q)
    ).select_related('category').prefetch_related('images')[:8]
    results = []
    for p in products:
        img = p.primary_image
        results.append({
            'name': p.name,
            'url': f'/products/{p.slug}/',
            'image': img.image.url if img else '',
            'price': str(p.current_price),
            'category': p.category.name if p.category else '',
        })
    return JsonResponse(results, safe=False)


def category_list(request):
    sections = Category.objects.filter(is_active=True, parent=None).prefetch_related('children').order_by('order', 'name')
    return render(request, 'products/categories.html', {'sections': sections})


@login_required
def favorite_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
    is_fav = created

    if request.headers.get('HX-Request'):
        referer = request.META.get('HTTP_REFERER', '')
        if product.slug in referer and 'list' not in referer and 'favorites' not in referer:
            return render(request, 'products/partials/fav_btn_detail.html', {
                'product': product, 'is_fav': is_fav,
            })
        return render(request, 'products/partials/fav_btn.html', {
            'product': product, 'is_fav': is_fav,
        })
    return redirect(request.META.get('HTTP_REFERER', 'products:list'))


@login_required
def favorite_list(request):
    fav_products = Product.objects.filter(
        favorites__user=request.user, is_active=True
    ).prefetch_related('images', 'variants').select_related('category')
    favorite_ids = set(fav_products.values_list('pk', flat=True))
    return render(request, 'products/favorites.html', {
        'products': fav_products,
        'favorite_ids': favorite_ids,
    })


def get_variant_stock(request, variant_id):
    try:
        variant = ProductVariant.objects.get(pk=variant_id)
        return JsonResponse({'stock': variant.stock, 'in_stock': variant.in_stock})
    except ProductVariant.DoesNotExist:
        return JsonResponse({'stock': 0, 'in_stock': False})