from django.core.cache import cache
from products.models import Category


def navigation(request):
    """Provides nav_sections (all active categories) to every template."""
    key = 'nav_sections'
    sections = cache.get(key)
    if sections is None:
        sections = list(
            Category.objects.filter(is_active=True)
            .order_by('order', 'name')
        )
        cache.set(key, sections, 60 * 60)  # 1 hour
    return {'nav_sections': sections}