"""
Click.uz Payment Integration
Docs: https://docs.click.uz/

Flow:
  1. User clicks "Pay via Click" → redirect to click.uz checkout URL
  2. Click sends Prepare request (before payment) → we validate
  3. Click sends Complete request (after payment) → we confirm

Both Prepare and Complete are POST requests to our endpoint.
"""
import hashlib
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from orders.models import Order
from .models import Payment

logger = logging.getLogger(__name__)

# Click error codes
CLICK_OK = 0
CLICK_ERR_BAD_REQUEST = -8
CLICK_ERR_NOT_FOUND = -5
CLICK_ERR_ALREADY_PAID = -4
CLICK_ERR_CANCELLED = -9


def _check_sign(data: dict, action: int) -> bool:
    """Verify Click.uz signature."""
    sign_string = '{click_trans_id}{service_id}{SECRET_KEY}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}'.format(
        click_trans_id=data.get('click_trans_id', ''),
        service_id=data.get('service_id', ''),
        SECRET_KEY=settings.CLICK_SECRET_KEY,
        merchant_trans_id=data.get('merchant_trans_id', ''),
        merchant_prepare_id=data.get('merchant_prepare_id', '') if action == 1 else '',
        amount=data.get('amount', ''),
        action=action,
        sign_time=data.get('sign_time', ''),
    )
    expected = hashlib.md5(sign_string.encode()).hexdigest()
    return data.get('sign_string') == expected


@csrf_exempt
@require_POST
def click_webhook(request):
    """Handle both Prepare (action=0) and Complete (action=1) from Click."""
    import json

    try:
        if request.content_type and 'json' in request.content_type:
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
    except Exception:
        return JsonResponse({'error': CLICK_ERR_BAD_REQUEST, 'error_note': 'Bad request'})

    action = int(data.get('action', -1))
    order_number = data.get('merchant_trans_id', '')
    amount = float(data.get('amount', 0))
    click_trans_id = data.get('click_trans_id', '')

    logger.info('Click action=%s order=%s amount=%s', action, order_number, amount)

    # Validate signature
    if not _check_sign(data, action):
        return JsonResponse({'error': -1, 'error_note': 'SIGN CHECK FAILED!'})

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return JsonResponse({'error': CLICK_ERR_NOT_FOUND, 'error_note': 'Order not found'})

    expected_amount = float(order.total)
    if abs(amount - expected_amount) > 1:
        return JsonResponse({'error': -2, 'error_note': 'Incorrect amount'})

    if action == 0:
        # Prepare: validate order before payment
        if order.payments.filter(status=Payment.STATUS_PAID).exists():
            return JsonResponse({'error': CLICK_ERR_ALREADY_PAID, 'error_note': 'Already paid'})

        payment = Payment.objects.create(
            order=order,
            provider=Payment.PROVIDER_CLICK,
            amount=int(amount * 100),
            provider_transaction_id=click_trans_id,
            status=Payment.STATUS_WAITING,
            request_data=data,
        )
        return JsonResponse({
            'click_trans_id': click_trans_id,
            'merchant_trans_id': order_number,
            'merchant_prepare_id': payment.pk,
            'error': CLICK_OK,
            'error_note': 'Success',
        })

    elif action == 1:
        # Complete: confirm payment
        merchant_prepare_id = data.get('merchant_prepare_id')
        try:
            payment = Payment.objects.get(pk=merchant_prepare_id, provider=Payment.PROVIDER_CLICK)
        except Payment.DoesNotExist:
            return JsonResponse({'error': CLICK_ERR_NOT_FOUND, 'error_note': 'Prepare not found'})

        error_code = int(data.get('error', 0))
        if error_code < 0:
            payment.status = Payment.STATUS_CANCELLED
            payment.save()
            return JsonResponse({
                'click_trans_id': click_trans_id,
                'merchant_trans_id': order_number,
                'merchant_confirm_id': payment.pk,
                'error': CLICK_OK,
                'error_note': 'Cancelled',
            })

        payment.status = Payment.STATUS_PAID
        payment.paid_at = timezone.now()
        payment.save()

        order.status = Order.STATUS_CONFIRMED
        order.save()

        return JsonResponse({
            'click_trans_id': click_trans_id,
            'merchant_trans_id': order_number,
            'merchant_confirm_id': payment.pk,
            'error': CLICK_OK,
            'error_note': 'Success',
        })

    return JsonResponse({'error': CLICK_ERR_BAD_REQUEST, 'error_note': 'Invalid action'})


def get_click_payment_url(order: Order) -> str:
    """Generate Click.uz redirect URL for payment."""
    base = "https://my.click.uz/services/pay"
    return (
        f"{base}"
        f"?service_id={settings.CLICK_SERVICE_ID}"
        f"&merchant_id={settings.CLICK_MERCHANT_ID}"
        f"&amount={order.total}"
        f"&transaction_param={order.order_number}"
        f"&return_url={settings.SITE_URL}/orders/success/{order.order_number}/"
    )


def get_payme_payment_url(order: Order) -> str:
    """Generate Payme checkout URL."""
    import base64
    import json
    params = json.dumps({
        'm': settings.PAYME_MERCHANT_ID,
        'ac.order_number': order.order_number,
        'a': int(order.total * 100),
        'l': 'ru',
    })
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"