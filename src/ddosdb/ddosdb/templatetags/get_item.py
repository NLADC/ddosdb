from django import template

register = template.Library()


@register.filter(name='get_item')
def multiply(value, arg):
    return value.get(arg)
