from .cart import Cart
from products.models import ProductVariant


def cart(request):
    c = Cart(request)
    product_ids = set()
    if c.cart:
        variant_ids = list(c.cart.keys())
        product_ids = set(
            ProductVariant.objects.filter(id__in=variant_ids)
            .values_list('product_id', flat=True)
        )
    return {'cart': c, 'cart_product_ids': product_ids}
