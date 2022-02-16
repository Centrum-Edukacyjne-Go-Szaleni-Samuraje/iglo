import requests


class OGSException(Exception):
    pass


def fetch_sgf(sgf_url: str) -> str:
    response = requests.get(url=sgf_url)
    if response.status_code != 200:
        raise OGSException("can not fetch SGF file")
    return response.content.decode()
