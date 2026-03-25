from decimal import Decimal
from django.conf import settings
from products.models import ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, variant, quantity=1, override_quantity=False):
        variant_id = str(variant.id)
        if variant_id not in self.cart:
            self.cart[variant_id] = {
                'quantity': 0,
                'price': str(variant.product.current_price),
                'product_name': variant.product.name,
                'size_name': variant.size.name,
                'color_name': variant.color.name,
            }
        if override_quantity:
            self.cart[variant_id]['quantity'] = quantity
        else:
            self.cart[variant_id]['quantity'] += quantity
        self.save()

    def remove(self, variant_id):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def update(self, variant_id, quantity):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            if quantity <= 0:
                self.remove(variant_id)
            else:
                self.cart[variant_id]['quantity'] = quantity
                self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self):
        variant_ids = self.cart.keys()
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related(
            'product', 'size', 'color'
        ).prefetch_related('product__images')
        variant_map = {str(v.id): v for v in variants}
        for variant_id, data in self.cart.items():
            variant = variant_map.get(variant_id)
            if not variant:
                continue
            price = Decimal(data['price'])
            yield {
                **data,
                'variant': variant,
                'price': price,
                'total_price': price * data['quantity'],
            }

    def __bool__(self):
        return bool(self.cart)
