from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def price(value):
    if isinstance(value, Decimal):
        return f"{value:7,} грн.".replace(",", " ")

    return "0 грн."
