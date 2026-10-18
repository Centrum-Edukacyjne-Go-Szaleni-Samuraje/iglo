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


def upload_sgf(config: AISenseiConfig, sgf_data: str, tags: list[str]) -> str:
    response_token = requests.post(
        url=config.auth_url,
        data={
            "email": config.email,
            "password": config.password,
            "returnSecureToken": True,
        },
    )

    if response_token.status_code != 200:
        raise AISenseiException(
            f"authentication error (HTTP {response_token.status_code}): {response_token.text}"
        )

    response_upload = requests.post(
        url=config.service_url,
        json={
            "token": response_token.json()["idToken"],
            "game": sgf_data,
            "options": {"quality": "free"},
            "tags": tags
        },
    )
    if response_upload.status_code != 200:
        raise AISenseiException(
            f"upload error (HTTP {response_upload.status_code}): {response_upload.text}"
        )

    upload_data = response_upload.json()
    if "error" in upload_data:
        raise AISenseiException(f"upload error: {upload_data['error']}")

    return upload_data["url"]
