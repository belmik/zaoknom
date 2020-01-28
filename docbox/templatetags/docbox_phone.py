from django import template

register = template.Library()


@register.filter
def phone(value):
    if not value:
        return ""

    return f"({value[:3]}) {value[3:6]} {value[6:]}"
