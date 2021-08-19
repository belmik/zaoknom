import logging
import os

import requests

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_SEND_MESSAGE_URL = os.getenv("BOT_SEND_MESSAGE_URL")


def send_delivery_info(orders: list) -> None:
    grouped_orders = group_orders_by_delivery_date(orders)
    messages = create_delivery_messages(grouped_orders)
    send_message_to_bot(messages)


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


def send_message_to_bot(data):
    if not BOT_TOKEN or not BOT_SEND_MESSAGE_URL:
        logger.error("Can't send message to the bot because environment var BOT_TOKEN or BOT_SEND_MESSAGE_URL not set")
        return False

    auth_header = {"Authorization": "Bearer " + BOT_TOKEN}
    try:
        requests.post(BOT_SEND_MESSAGE_URL, json=data, headers=auth_header, timeout=5)
    except Exception as e:
        logger.error(f"Got error during request to the bot: {e}")
        return False
    return True
