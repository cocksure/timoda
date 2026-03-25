from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product_name', 'size_name', 'color_name', 'price', 'quantity', 'total_price']
    extra = 0

    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Итого'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'city', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Заказ', {'fields': ('order_number', 'status', 'user')}),
        ('Покупатель', {'fields': ('full_name', 'email', 'phone')}),
        ('Доставка', {'fields': ('shipping_address', 'city', 'postal_code', 'country')}),
        ('Стоимость', {'fields': ('subtotal', 'shipping_cost', 'total')}),
        ('Примечания', {'fields': ('notes',)}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )