from django import template

register = template.Library()


@register.filter
def get_range(value):
    """
    Generate a range of numbers from 0 to value-1.
    Usage: {% for i in count|get_range %}
    """
    return range(value)


@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using the key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key, "")