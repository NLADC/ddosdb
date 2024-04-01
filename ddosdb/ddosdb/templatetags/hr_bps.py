from django import template
# import math

register = template.Library()

def bps_to_human_readable(num, suffix='b/s'):
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.0f}Yi{suffix}"

@register.filter(name='hr_bps')
def hr_bps(value, arg="b/s"):
    return bps_to_human_readable(float(value), suffix=arg)
    # return "{:.{}f}".format( value, arg )
