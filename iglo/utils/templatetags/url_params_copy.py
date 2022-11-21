from django.template import RequestContext
from django.template.defaultfilters import register


@register.simple_tag(takes_context=True)
def url_params_copy(context: RequestContext, **kwargs) -> str:
    params = context['request'].GET.copy()
    for k, v in kwargs.items():
        if not isinstance(v, list):
            v = [v]
        params.setlist(k, v)
    return params.urlencode()
