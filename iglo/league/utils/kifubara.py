from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class KifubaraConfig:
    service_url: str
    key: str


class KifubaraException(Exception):
    pass


def upload_game_to_kifubara(
    config: KifubaraConfig,
    sgf_data: str,
    match_id: str,
    season: Optional[str] = None,
    group: Optional[str] = None,
    round: Optional[str] = None,
    black: Optional[str] = None,
    white: Optional[str] = None,
    board: Optional[str] = None,
    external_url: Optional[str] = None,
) -> str:
    payload = {
        "sgf": sgf_data,
        "match_id": match_id,
    }
    if season:
        payload["season"] = str(season)
    if group:
        payload["group"] = str(group)
    if round:
        payload["round"] = str(round)
    if black:
        payload["black"] = str(black)
    if white:
        payload["white"] = str(white)
    if board:
        payload["board"] = str(board)
    if external_url:
        payload["external_url"] = str(external_url)

    response = requests.post(
        url=config.service_url,
        headers={
            "Authorization": f"Bearer {config.key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise KifubaraException(
            f"upload error (HTTP {response.status_code}): {response.text}"
        )

    data = response.json()
    if "error" in data:
        raise KifubaraException(f"upload error: {data['error']}")

    share_url = data.get("share_url")
    if not share_url:
        raise KifubaraException(f"unexpected response without share_url: {data}")

    return share_url
