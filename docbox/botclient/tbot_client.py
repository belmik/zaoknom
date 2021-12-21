import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_delivery_info(orders: list) -> None:
    grouped_orders = group_orders_by_delivery_date(orders)
    messages = create_delivery_messages(grouped_orders)
    for message in messages:
        send_message_to_bot(message)


def group_orders_by_delivery_date(orders):
    grouped_orders = {}
    for order in orders:
        if order.delivery_date not in grouped_orders:
            grouped_orders.update({order.delivery_date: [order]})
            continue
        grouped_orders[order.delivery_date].append(order)

    return grouped_orders


def create_delivery_messages(grouped_orders):
    messages = []
    for delivery_date, orders_list in grouped_orders.items():
        message = f"Доставка {delivery_date.isoformat()}\n\n\n"
        for provider_order in orders_list:
            message += f"{provider_order.code}: {provider_order.order.client.name}\n"
            message += f"{provider_order.order_content}\n\n"
            messages.append(message)

    return messages


def send_message_to_bot(message):
    try:
        requests.post(
            settings.TELEGRAM_SEND_MESSAGE_URL,
            json={"chat_id": settings.TELEGRAM_ZAOKNOM_CHAT_ID, "text": message},
            timeout=5,
        )
    except Exception as e:
        logger.error(f"Got error during request to the bot: {e}")
        return False
    return True
