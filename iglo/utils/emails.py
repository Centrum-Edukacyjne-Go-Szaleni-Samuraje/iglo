from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template


def send_email(
        subject_template: str,
        body_template: str,
        context: dict[str, Any],
        to: list[str],
        **kwargs,
):
    context = context | {"domain": "https://" + settings.DOMAIN}
    subject = get_template(subject_template).render(context).strip()
    body = get_template(body_template).render(context)
    msg = EmailMessage(subject=subject, body=body, to=to, **kwargs)
    msg.content_subtype = "html"
    msg.send()
