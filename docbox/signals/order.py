def update_status(sender, **kwargs):
    provider_order = kwargs["instance"]
    order = provider_order.order

    provider_statues = order.get_provider_orders_statuses()

    if len(provider_statues) == 1:
        order.status = provider_statues.pop()
        order.save()
