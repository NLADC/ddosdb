from django import template
import math

register = template.Library()


@register.filter(name='precision')
def precision(value, arg):
    return "{:.{}f}".format( value, arg )
