import datetime
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

import requests
import unicodedata


class TournamentClass(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass(frozen=True)
class DatesRange:
    start: datetime.date
    end: datetime.date


@dataclass(frozen=True)
class ByoYomi:
    duration: int
    periods: int


@dataclass(frozen=True)
class TimeLimit:
    basic: int
    byo_yomi: Optional[ByoYomi]


@dataclass(frozen=True)
class Player:
    first_name: str
    last_name: str
    rank: str
    country: str
    club: str
    pin: str


@dataclass(frozen=True)
class Game:
    white: Optional[Player]
    black: Optional[Player]
    winner: Player


@dataclass(frozen=True)
class Location:
    country: str
    city: str


def create_tournament_table(
    klass: TournamentClass,
    name: str,
    location: Location,
    dates: DatesRange,
    handicap: Optional[str],
    komi: Decimal,
    time_limit: TimeLimit,
    players: list[Player],
    rounds: list[list[Game]],
):
    tm = time_limit.basic
    if time_limit.byo_yomi:
        tm += 45 * (time_limit.byo_yomi.duration / 60)
    lines = [
        f"; CL[{klass.value}]",
        f"; EV[{name}]",
        f"; PC[{location.country}, {location.city}]",
        f"; DT[{dates.start},{dates.end}]",
        "; HA[h9]" if not handicap else "",
        f"; KM[{komi}]",
        f"; TM[{tm}]",
        ";",
    ]
    max_name_width = max(len(player.first_name) + len(player.last_name) + 1 for player in players)
    place_width = len(str(len(players)))
    for place, player in enumerate(players, start=1):
        name = _strip_local_chars(player.last_name) + " " + _strip_local_chars(player.first_name)
        line = f"{place:<{place_width}} {name:<{max_name_width}}  {player.rank:<3} {player.country} {player.club:<4}  "
        wins = 0
        results = ""
        for round in rounds:
            result_width = place_width + 5
            player_found_in_round = False
            
            # Handle empty rounds (no EGD-eligible games in this round)
            if not round:
                results += "0-".ljust(result_width)
                continue
                
            for game in round:
                if game.winner == player:
                    wins += 1
                if player in [game.black, game.white, game.winner]:
                    player_found_in_round = True
                    if not game.black and not game.white and game.winner == player:
                        results += "0+".ljust(result_width)
                    elif game.winner is None:
                        results += "0-".ljust(result_width)
                    else:
                        opponent = game.black if player == game.white else game.white
                        opponent_place = players.index(opponent) + 1
                        result = "+" if player == game.winner else "-"
                        color = "b" if player == game.black else "w"
                        results += f"{opponent_place}{result}/{color}".ljust(result_width)
            
            # Add "did not play" indicator if player didn't participate in this round
            if not player_found_in_round:
                results += "0-".ljust(result_width)
        stats = "  ".join(
            [
                str(wins),
                "0",
                "0",
                "0",
            ]
        )
        line += f"{stats}  {results}|{player.pin}"
        lines.append(line)
    return "\n".join(lines)


def _strip_local_chars(text: str) -> str:
    return unicodedata.normalize("NFKD", text.replace("Ł", "L").replace("ł", "l")).encode("ASCII", "ignore").decode()


def gor_to_rank(gor: Optional[int]) -> str:
    if gor is None:
        raise ValueError("Cannot convert None to rank. Player is missing rank information.")
        
    if gor <= 2050:
        result = -((gor - 50) // 100) + 20
        return f"{result}k"
    else:
        result = ((gor - 50) // 100) - 19
        return f"{result}d"


class EGDException(Exception):
    pass


@dataclass(frozen=True)
class EGDPlayerData:
    """Comprehensive player data from EGD."""
    pin: str
    first_name: str
    last_name: str
    country_code: str
    club: str
    grade: str
    gor: int
    last_appearance: str
    total_tournaments: int
    egf_placement: Optional[int] = None


def get_player_data_by_pin(pin: str) -> EGDPlayerData:
    """
    Fetch comprehensive player data from EGD by PIN.
    
    Returns:
        EGDPlayerData object containing all relevant player information
    
    Raises:
        EGDException: If the EGD API returns an error or player data cannot be fetched
    """
    url = f'http://www.europeangodatabase.eu/EGD/GetPlayerDataByPIN.php?pin={pin}'
    response = requests.get(url)
    if response.status_code != 200:
        raise EGDException(f'EGD is responding with {response.status_code}')
    
    content = response.json()
    
    if content.get('retcode') != 'Ok':
        raise EGDException(f'EGD returned error: {content.get("retcode", "Unknown error")}')
    
    try:
        # Use Real_Name and Real_Last_Name if available, otherwise fall back to Name and Last_Name
        first_name = content.get('Real_Name', content.get('Name', ''))
        last_name = content.get('Real_Last_Name', content.get('Last_Name', ''))
        
        return EGDPlayerData(
            pin=pin,
            first_name=first_name,
            last_name=last_name,
            country_code=content.get('Country_Code', ''),
            club=content.get('Club', ''),
            grade=content.get('Grade', ''),
            gor=int(content['Gor']),
            last_appearance=content.get('Last_Appearance', ''),
            total_tournaments=int(content.get('Tot_Tournaments', 0)),
            egf_placement=int(content['EGF_Placement']) if content.get('EGF_Placement') else None
        )
    except (KeyError, ValueError) as e:
        raise EGDException(f'Cannot parse player data: {str(e)}')


def get_gor_by_pin(pin: str) -> int:
    """
    Fetch player's GoR (Go Rating) from EGD by PIN.
    
    For backward compatibility. Uses get_player_data_by_pin internally.
    
    Returns:
        int: Player's GoR rating
        
    Raises:
        EGDException: If the player data cannot be fetched or GoR is missing
    """
    try:
        player_data = get_player_data_by_pin(pin)
        return player_data.gor
    except EGDException:
        raise
    except Exception as e:
        raise EGDException(f'Cannot fetch player GoR: {str(e)}')
