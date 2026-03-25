from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from .cart import Cart
from products.models import ProductVariant


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


@require_POST
def cart_add(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant.objects.select_related('product', 'size', 'color'), pk=variant_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(variant, quantity=quantity)

    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_icon.html', {'cart': cart})
    return redirect('cart:detail')


@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    cart.remove(variant_id)

    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_table.html', {'cart': cart})
    return redirect('cart:detail')


@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart.update(variant_id, quantity)

    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_table.html', {'cart': cart})
    return redirect('cart:detail')