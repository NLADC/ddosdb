from django import template

register = template.Library()

@register.filter(name='short_list')
def short_list(value, arg):
    if arg == 0:
        return short_list_trunc(value)
    return short_list_long(value)

def short_list_trunc(value):
    result = []
    for it in value:
        result.append(shorten(it))
    return ', '.join(result)


def shorten(tag):
    result = ''
    if "_" in tag:
        tag_elms = tag.split('_')
        tag_bits = []
        for te in tag_elms:
            tag_bits.append(te[0])
        result = '_'.join(tag_bits)
    else:
        result = tag[:3]
    return result

def short_list_long(value):
    return ', '.join(value)
