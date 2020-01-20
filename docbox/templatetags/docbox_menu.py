from collections import namedtuple

from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("docbox/main-menu.html", takes_context=True)
def main_menu(context):
    MenuItem = namedtuple("MenuItem", "name, url, fa_icon_name, add_url, active_link_cls")
    menu = [
        ("Заказы", "docbox:orders-list", "fa-copy", "docbox:new-order"),
        ("Клиенты", "docbox:clients-list", "fa-users", ""),
        ("Бухгалтерия", "docbox:bookkeeping-orders", "fa-book", ""),
    ]

    active_class_name = " active"

    current_url_name = None
    match = context.request.resolver_match
    if match:
        current_url_name = f"{match.namespace}:{match.url_name}"

    menu_list = []

    for name, url_name, fa_icon_name, add_url_name in menu:
        url = reverse(url_name)

        add_url = ""
        if add_url_name:
            add_url = reverse(add_url_name)

        active_link_cls = ""
        if url_name == current_url_name:
            active_link_cls = active_class_name

        menu_list.append(MenuItem(name, url, fa_icon_name, add_url, active_link_cls))

    return {"menu": menu_list}
