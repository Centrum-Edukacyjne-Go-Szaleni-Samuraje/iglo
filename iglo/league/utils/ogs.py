import requests
from typing import Optional, Dict, Any, Tuple


class OGSException(Exception):
    pass


def fetch_sgf(sgf_url: str) -> str:
    response = requests.get(url=sgf_url)
    if response.status_code != 200:
        raise OGSException("can not fetch SGF file")
    return response.content.decode()


def get_player_data(username: str) -> Dict[str, Any]:
    """
    Get complete player data from OGS by username.

    Args:
        username: The OGS username to look up

    Returns:
        A dictionary with player data including ID, rating, and deviation

    Raises:
        OGSException: If there's an error communicating with the OGS API
    """
    try:
        # First get the player ID
        response = requests.get(f"https://online-go.com/api/v1/players?username={username}")
        response.raise_for_status()

        data = response.json()
        if data.get('count', 0) == 0 or not data.get('results'):
            raise OGSException(f"Player '{username}' not found")

        if len(data['results']) != 1:
            raise OGSException(f"Unexpected result from https://online-go.com/api/v1/players?username={username} :\n{data}")

        player_id = data['results'][0]['id']

        # Now get the detailed player data
        response = requests.get(f"https://online-go.com/api/v1/players/{player_id}")
        if response.status_code != 200:
            raise OGSException(f"Failed to fetch player details: HTTP {response.status_code}")

        player_data = response.json()

        # Extract the rating information
        result = {
            'id': player_id,
            'rating': None,
            'deviation': None,
            'profile_url': f"https://online-go.com/player/{player_id}"
        }

        # Get the overall rating (not per-speed ratings)
        if 'ratings' in player_data and 'overall' in player_data['ratings']:
            result['rating'] = player_data['ratings']['overall'].get('rating')
            result['deviation'] = player_data['ratings']['overall'].get('deviation')

        return result

    except requests.RequestException as e:
        raise OGSException(f"Error communicating with OGS API: {str(e)}")
    except (ValueError, KeyError) as e:
        raise OGSException(f"Invalid response from OGS API: {str(e)}")
