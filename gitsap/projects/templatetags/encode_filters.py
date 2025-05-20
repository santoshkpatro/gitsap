from django import template
from urllib.parse import quote

register = template.Library()


@register.filter
def full_urlencode(value):
    return quote(value, safe="")  # encode EVERYTHING including "/"
