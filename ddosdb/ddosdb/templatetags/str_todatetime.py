from django import template
from datetime import datetime

register = template.Library()

@register.filter(name='str_todatetime')
def str_todatetime(value):
    if type(value) is str:
        # Remove any + or in the string (timezone offset)
        val = value.partition('+')[0]
        # remove the subsecond part if it exists
        val = val.partition('.')[0]
        # return datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
        return datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')

    return datetime.strptime("1970-01-01T00:00:00.0000", '%Y-%m-%dT%H:%M:%S.%f')
