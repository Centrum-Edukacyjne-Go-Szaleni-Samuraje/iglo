import re

import requests
from django.conf import settings


class OGSException(Exception):
    pass


def fetch_sgf(game_url: str) -> str:
    match = re.match(settings.OGS_GAME_LINK_REGEX, game_url)
    if not match:
        raise OGSException("wrong game url format")
    response = requests.get(url=settings.OGS_SGF_LINK_FORMAT.format(id=match.group(1)))
    if response.status_code != 200:
        raise OGSException("can not fetch SGF file")
    return response.content.decode()
