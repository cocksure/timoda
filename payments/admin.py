from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'provider', 'amount_sum_display', 'status', 'created_at', 'paid_at']
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['order__order_number', 'provider_transaction_id']
    readonly_fields = ['provider_transaction_id', 'request_data', 'response_data', 'created_at', 'paid_at']

    def amount_sum_display(self, obj):
        return f'{obj.amount_sum:,.0f} сум'
    amount_sum_display.short_description = 'Сумма'