from django.template.defaultfilters import register
from django.urls import translate_url as django_translate_url


@register.simple_tag(takes_context=True)
def translate_url(context, lang_code):
    try:
        path = context["request"].get_full_path()
        return django_translate_url(path, lang_code)
    except KeyError:
        return django_translate_url("/", lang_code)
