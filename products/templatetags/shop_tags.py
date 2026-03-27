from django import template

register = template.Library()


@register.filter(name='money')
def money(value):
    """Format number as Russian-style price: 190 000"""
    try:
        value = int(float(str(value)))
        return f"{value:,}".replace(",", "\u00a0")
    except (ValueError, TypeError):
        return value
