from django import template

register = template.Library()


@register.filter
def get_range(value):
    """
    Generate a range of numbers from 0 to value-1.
    Usage: {% for i in count|get_range %}
    """
    return range(value)