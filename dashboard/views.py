from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from products.models import Product, Category, ProductVariant, ProductImage, Color
from orders.models import Order, PickupPoint
from core.models import Banner
from django import forms


def _clear_product_cache(slug=None):
    cache.delete('home_page_data')
    if slug:
        cache.delete(f'product_detail_{slug}')


def dashboard_view(view_func):
    return staff_member_required(view_func, login_url='/accounts/login/')


# ── Forms ────────────────────────────────────────────────────

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'slug', 'description', 'composition',
            'care_instructions', 'price', 'sale_price',
            'is_featured', 'is_new', 'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'care_instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-control')


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size', 'color', 'stock', 'sku']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control form-control-sm')


# ── Home / Stats ─────────────────────────────────────────────

@dashboard_view
def home(request):
    today = timezone.now().date()
    last_30 = today - timedelta(days=30)

    stats = {
        'orders_today': Order.objects.filter(created_at__date=today).count(),
        'orders_month': Order.objects.filter(created_at__date__gte=last_30).count(),
        'revenue_month': Order.objects.filter(
            created_at__date__gte=last_30,
            status__in=[Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]
        ).aggregate(t=Sum('total'))['t'] or 0,
        'products_total': Product.objects.filter(is_active=True).count(),
        'low_stock': ProductVariant.objects.filter(stock__gt=0, stock__lte=5).count(),
        'out_of_stock': ProductVariant.objects.filter(stock=0).count(),
        'pending_orders': Order.objects.filter(status=Order.STATUS_PENDING).count(),
    }
    recent_orders = Order.objects.select_related('user').prefetch_related('items')[:8]
    return render(request, 'dashboard/home.html', {'stats': stats, 'recent_orders': recent_orders})


# ── Products ─────────────────────────────────────────────────

@dashboard_view
def product_list(request):
    q = request.GET.get('q', '')
    products = Product.objects.select_related('category').prefetch_related('images', 'variants')
    if q:
        products = products.filter(name__icontains=q)
    return render(request, 'dashboard/products/list.html', {'products': products, 'q': q})


@dashboard_view
def product_add(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save()
        _clear_product_cache()
        messages.success(request, f'Товар «{product.name}» создан.')
        return redirect('dashboard:product_edit', pk=product.pk)
    return render(request, 'dashboard/products/form.html', {'form': form, 'title': 'Добавить товар'})


@dashboard_view
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)

    if 'save_product' in request.POST and form.is_valid():
        form.save()
        _clear_product_cache(slug=product.slug)
        messages.success(request, 'Товар сохранён.')
        return redirect('dashboard:product_edit', pk=pk)

    if 'upload_image' in request.POST and request.FILES.get('image'):
        img = ProductImage(product=product, image=request.FILES['image'])
        if not product.images.filter(is_primary=True).exists():
            img.is_primary = True
        color_id = request.POST.get('image_color')
        if color_id:
            img.color_id = int(color_id)
        img.save()
        messages.success(request, 'Фото загружено.')
        return redirect('dashboard:product_edit', pk=pk)

    variant_form = ProductVariantForm(prefix='var')
    if 'add_variant' in request.POST:
        variant_form = ProductVariantForm(request.POST, prefix='var')
        if variant_form.is_valid():
            v = variant_form.save(commit=False)
            v.product = product
            v.save()
            messages.success(request, 'Вариант добавлен.')
            return redirect('dashboard:product_edit', pk=pk)

    return render(request, 'dashboard/products/form.html', {
        'form': form,
        'product': product,
        'variant_form': variant_form,
        'colors': Color.objects.all(),
        'title': f'Редактировать: {product.name}',
    })


@dashboard_view
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        _clear_product_cache(slug=product.slug)
        product.delete()
        messages.success(request, f'Товар удалён.')
        return redirect('dashboard:product_list')
    return render(request, 'dashboard/confirm_delete.html', {'name': product.name})


@dashboard_view
def image_delete(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    product_pk = img.product_id
    if request.method == 'POST':
        img.image.delete(save=False)
        img.delete()
    return redirect('dashboard:product_edit', pk=product_pk)


@dashboard_view
def image_set_primary(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    product_pk = img.product_id
    ProductImage.objects.filter(product_id=product_pk).update(is_primary=False)
    img.is_primary = True
    img.save()
    return redirect('dashboard:product_edit', pk=product_pk)


@dashboard_view
def variant_update_stock(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    if request.method == 'POST':
        try:
            variant.stock = max(0, int(request.POST.get('stock', variant.stock)))
            variant.save()
        except ValueError:
            pass
    return redirect('dashboard:product_edit', pk=variant.product_id)


@dashboard_view
def variant_delete(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    product_pk = variant.product_id
    if request.method == 'POST':
        variant.delete()
    return redirect('dashboard:product_edit', pk=product_pk)


# ── Orders ───────────────────────────────────────────────────

@dashboard_view
def order_list(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.select_related('user').prefetch_related('items')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/orders/list.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    })


@dashboard_view
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items', 'payments'), pk=pk
    )
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус: {order.get_status_display()}')
            return redirect('dashboard:order_detail', pk=pk)
    return render(request, 'dashboard/orders/detail.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    })


# ── Banners ──────────────────────────────────────────────────

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'button_text', 'button_link',
                  'image', 'image_mobile', 'video', 'is_active', 'order']
        widgets = {
            'subtitle': forms.TextInput(),
            'button_link': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-control')


@dashboard_view
def banner_list(request):
    banners = Banner.objects.all()
    return render(request, 'dashboard/banners/list.html', {'banners': banners})


@dashboard_view
def banner_add(request):
    form = BannerForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        cache.delete('home_page_data')
        messages.success(request, 'Баннер добавлен.')
        return redirect('dashboard:banner_list')
    return render(request, 'dashboard/banners/form.html', {'form': form, 'title': 'Добавить баннер'})


@dashboard_view
def banner_edit(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    form = BannerForm(request.POST or None, request.FILES or None, instance=banner)
    if form.is_valid():
        form.save()
        cache.delete('home_page_data')
        messages.success(request, 'Баннер сохранён.')
        return redirect('dashboard:banner_list')
    return render(request, 'dashboard/banners/form.html', {
        'form': form, 'banner': banner, 'title': 'Редактировать баннер'
    })


@dashboard_view
def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        cache.delete('home_page_data')
        banner.delete()
        messages.success(request, 'Баннер удалён.')
        return redirect('dashboard:banner_list')
    return render(request, 'dashboard/confirm_delete.html', {'name': banner.title})


# ── Pickup Points ─────────────────────────────────────────────

class PickupPointForm(forms.ModelForm):
    class Meta:
        model = PickupPoint
        fields = ['name', 'address', 'city', 'working_hours', 'phone',
                  'latitude', 'longitude', 'is_active', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-control')


@dashboard_view
def pickup_list(request):
    points = PickupPoint.objects.all()
    return render(request, 'dashboard/pickups/list.html', {'points': points})


@dashboard_view
def pickup_edit(request, pk=None):
    point = get_object_or_404(PickupPoint, pk=pk) if pk else None
    form = PickupPointForm(request.POST or None, instance=point)
    if form.is_valid():
        form.save()
        messages.success(request, 'Пункт выдачи сохранён.')
        return redirect('dashboard:pickup_list')
    title = 'Редактировать пункт выдачи' if point else 'Добавить пункт выдачи'
    return render(request, 'dashboard/pickups/form.html', {'form': form, 'point': point, 'title': title})


@dashboard_view
def pickup_delete(request, pk):
    point = get_object_or_404(PickupPoint, pk=pk)
    if request.method == 'POST':
        point.delete()
        messages.success(request, 'Пункт выдачи удалён.')
        return redirect('dashboard:pickup_list')
    return render(request, 'dashboard/confirm_delete.html', {'name': point.name})