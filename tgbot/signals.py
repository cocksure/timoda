import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='orders.Order')
def order_saved(sender, instance, created, **kwargs):
    """Notify on new order and status changes."""
    from tgbot.service import notify_new_order, notify_order_status

    if created:
        try:
            notify_new_order(instance)
        except Exception as e:
            logger.error(f'Telegram notify_new_order failed: {e}')
        return

    # Status changed? (tracked via Order._original_status)
    if hasattr(instance, '_original_status') and instance.status != instance._original_status:
        try:
            notify_order_status(instance)
        except Exception as e:
            logger.error(f'Telegram notify_order_status failed: {e}')