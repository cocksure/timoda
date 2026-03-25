"""
Payme Business API (JSON-RPC 2.0)
Docs: https://developer.help.paycom.uz/

Methods:
  CheckPerformTransaction  — can we accept this payment?
  CreateTransaction        — create transaction
  PerformTransaction       — confirm payment
  CancelTransaction        — cancel payment
  CheckTransaction         — check transaction status
  GetStatement             — get transactions for a period
"""
import base64
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

# Payme error codes
ERR_INVALID_AMOUNT = -31001
ERR_TRANSACTION_NOT_FOUND = -31003
ERR_INVALID_STATE = -31008
ERR_METHOD_NOT_FOUND = -32601
ERR_CANT_PERFORM = -31008


def _check_auth(request) -> bool:
    """Verify Basic auth header from Payme."""
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(auth.split(' ')[1]).decode()
        _, password = decoded.split(':', 1)
        return password == settings.PAYME_KEY
    except Exception:
        return False


def _error(code: int, message: str, request_id=None) -> dict:
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'error': {'code': code, 'message': {'ru': message, 'uz': message, 'en': message}},
    }


def _result(data: dict, request_id=None) -> dict:
    return {'jsonrpc': '2.0', 'id': request_id, 'result': data}


def check_perform_transaction(params: dict, request_id) -> dict:
    amount = params.get('amount')
    account = params.get('account', {})
    order_number = account.get('order_number')

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return _error(-31050, 'Заказ не найден', request_id)

    expected = int(order.total * 100)  # convert to tiyin
    if amount != expected:
        return _error(ERR_INVALID_AMOUNT, f'Неверная сумма. Ожидается {expected} тийин', request_id)

    return _result({'allow': True}, request_id)


def create_transaction(params: dict, request_id) -> dict:
    amount = params.get('amount')
    account = params.get('account', {})
    order_number = account.get('order_number')
    transaction_id = params.get('id')
    time_ms = params.get('time')

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return _error(-31050, 'Заказ не найден', request_id)

    expected = int(order.total * 100)
    if amount != expected:
        return _error(ERR_INVALID_AMOUNT, 'Неверная сумма', request_id)

    payment, created = Payment.objects.get_or_create(
        provider=Payment.PROVIDER_PAYME,
        provider_transaction_id=transaction_id,
        defaults={
            'order': order,
            'amount': amount,
            'provider_time': time_ms,
            'status': Payment.STATUS_WAITING,
        }
    )

    if not created and payment.order != order:
        return _error(ERR_INVALID_STATE, 'Транзакция занята', request_id)

    return _result({
        'create_time': int(payment.created_at.timestamp() * 1000),
        'transaction': str(payment.pk),
        'state': 1,
    }, request_id)


def perform_transaction(params: dict, request_id) -> dict:
    transaction_id = params.get('id')
    try:
        payment = Payment.objects.get(
            provider=Payment.PROVIDER_PAYME,
            provider_transaction_id=transaction_id,
        )
    except Payment.DoesNotExist:
        return _error(ERR_TRANSACTION_NOT_FOUND, 'Транзакция не найдена', request_id)

    if payment.status == Payment.STATUS_PAID:
        return _result({
            'transaction': str(payment.pk),
            'perform_time': int(payment.paid_at.timestamp() * 1000),
            'state': 2,
        }, request_id)

    if payment.status != Payment.STATUS_WAITING:
        return _error(ERR_INVALID_STATE, 'Невозможно выполнить транзакцию', request_id)

    now = timezone.now()
    payment.status = Payment.STATUS_PAID
    payment.paid_at = now
    payment.save()

    # Mark order as confirmed
    order = payment.order
    order.status = Order.STATUS_CONFIRMED
    order.save()

    return _result({
        'transaction': str(payment.pk),
        'perform_time': int(now.timestamp() * 1000),
        'state': 2,
    }, request_id)


def cancel_transaction(params: dict, request_id) -> dict:
    transaction_id = params.get('id')
    try:
        payment = Payment.objects.get(
            provider=Payment.PROVIDER_PAYME,
            provider_transaction_id=transaction_id,
        )
    except Payment.DoesNotExist:
        return _error(ERR_TRANSACTION_NOT_FOUND, 'Транзакция не найдена', request_id)

    payment.status = Payment.STATUS_CANCELLED
    payment.save()

    return _result({
        'transaction': str(payment.pk),
        'cancel_time': int(timezone.now().timestamp() * 1000),
        'state': -1,
    }, request_id)


def check_transaction(params: dict, request_id) -> dict:
    transaction_id = params.get('id')
    try:
        payment = Payment.objects.get(
            provider=Payment.PROVIDER_PAYME,
            provider_transaction_id=transaction_id,
        )
    except Payment.DoesNotExist:
        return _error(ERR_TRANSACTION_NOT_FOUND, 'Транзакция не найдена', request_id)

    state_map = {
        Payment.STATUS_WAITING:   1,
        Payment.STATUS_PAID:      2,
        Payment.STATUS_CANCELLED: -1,
    }
    return _result({
        'create_time': int(payment.created_at.timestamp() * 1000),
        'perform_time': int(payment.paid_at.timestamp() * 1000) if payment.paid_at else 0,
        'cancel_time': 0,
        'transaction': str(payment.pk),
        'state': state_map.get(payment.status, 0),
    }, request_id)


METHODS = {
    'CheckPerformTransaction': check_perform_transaction,
    'CreateTransaction': create_transaction,
    'PerformTransaction': perform_transaction,
    'CancelTransaction': cancel_transaction,
    'CheckTransaction': check_transaction,
}


@csrf_exempt
@require_POST
def payme_webhook(request):
    import json
    if not _check_auth(request):
        return JsonResponse(_error(-32504, 'Не авторизован'), status=401)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse(_error(-32700, 'Parse error'))

    method = body.get('method')
    params = body.get('params', {})
    request_id = body.get('id')

    handler = METHODS.get(method)
    if not handler:
        return JsonResponse(_error(ERR_METHOD_NOT_FOUND, f'Метод не найден: {method}', request_id))

    logger.info('Payme %s: %s', method, params)
    result = handler(params, request_id)
    return JsonResponse(result)