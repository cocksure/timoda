from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.cart import Cart
from .models import Order, OrderItem, PickupPoint
from .forms import CheckoutForm


def checkout(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, 'Ваша корзина пуста.')
        return redirect('cart:detail')

    initial = {}
    if request.user.is_authenticated:
        initial = {
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
            'phone': request.user.phone,
        }
        default_address = request.user.addresses.filter(type='shipping', is_default=True).first()
        if default_address:
            initial.update({
                'shipping_address': default_address.address_line1,
                'city': default_address.city,
                'country': default_address.country,
                'postal_code': default_address.postal_code,
            })

    pickup_points = PickupPoint.objects.filter(is_active=True)
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == 'POST' and request.POST.get('delivery_method') == Order.DELIVERY_PICKUP:
        form.fields['shipping_address'].required = False
        form.fields['city'].required = False
    if form.is_valid():
        order = form.save(commit=False)
        order.subtotal = cart.get_total_price()
        order.total = order.subtotal + order.shipping_cost
        if request.user.is_authenticated:
            order.user = request.user
        delivery_method = request.POST.get('delivery_method', Order.DELIVERY_COURIER)
        order.delivery_method = delivery_method
        if delivery_method == Order.DELIVERY_PICKUP:
            pickup_id = request.POST.get('pickup_point_id')
            if pickup_id:
                try:
                    order.pickup_point = PickupPoint.objects.get(pk=pickup_id, is_active=True)
                    # For pickup, use pickup address as shipping address
                    order.shipping_address = order.pickup_point.address
                    order.city = order.pickup_point.city
                except PickupPoint.DoesNotExist:
                    pass
        try:
            lat = request.POST.get('latitude')
            lng = request.POST.get('longitude')
            if lat:
                order.latitude = float(lat)
            if lng:
                order.longitude = float(lng)
        except (ValueError, TypeError):
            pass
        order.save()

        for item in cart:
            OrderItem.objects.create(
                order=order,
                variant=item['variant'],
                product_name=item['variant'].product.name,
                size_name=item['variant'].size.name,
                color_name=item['variant'].color.name,
                price=item['price'],
                quantity=item['quantity'],
            )
            # Decrease stock
            item['variant'].stock = max(0, item['variant'].stock - item['quantity'])
            item['variant'].save()

        cart.clear()

        # If user chose online payment, redirect to payment provider
        payment_method = request.POST.get('payment_method', 'cash')
        if payment_method == 'payme':
            from payments.click import get_payme_payment_url
            return redirect(get_payme_payment_url(order))
        elif payment_method == 'click':
            from payments.click import get_click_payment_url
            return redirect(get_click_payment_url(order))

        return redirect('orders:success', order_number=order.order_number)

    from payments.click import get_click_payment_url, get_payme_payment_url
    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'pickup_points': pickup_points,
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/success.html', {'order': order})


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related('items').all()
    return render(request, 'orders/list.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__variant__product__images'),
        order_number=order_number, user=request.user
    )
    return render(request, 'orders/detail.html', {'order': order})