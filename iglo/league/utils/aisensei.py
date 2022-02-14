from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class AISenseiConfig:
    auth_url: str
    service_url: str
    email: str
    password: str


class AISenseiException(Exception):
    pass


def upload_sgf(config: AISenseiConfig, sgf_data: Optional[str] = None) -> str:
    response_token = requests.post(
        url=config.auth_url,
        data={
            "email": config.email,
            "password": config.password,
            "returnSecureToken": True,
        },
    )

    if response_token.status_code != 200:
        raise AISenseiException("authentication error")

    response_upload = requests.post(
        url=config.service_url,
        json={
            "token": response_token.json()["idToken"],
            "game": sgf_data,
            "options": {"quality": "pro"},
        },
    )
    if response_upload.status_code != 200:
        raise AISenseiException("upload error")

    return response_upload.json()["url"]
