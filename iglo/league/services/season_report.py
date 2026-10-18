import logging
import re
from typing import Optional

from league.models import Season, Game, WinType, Player

logger = logging.getLogger(__name__)


class SeasonReportService:
    @staticmethod
    def get_player_identifier(player: Player) -> str:
        """
        Returns EGD PIN if available, falling back to player nickname.
        """
        return player.egd_pin if player.egd_pin else player.nick

    @classmethod
    def transform_sgf(cls, raw_sgf: str, black_id: str, white_id: str) -> str:
        """
        Replaces PB[...] and PW[...] properties in raw_sgf with black_id and white_id.
        If PB or PW tag is missing, injects it into the root node.
        """
        content = raw_sgf

        # Replace PB if exists, else inject into root node
        if re.search(r'PB\[(?:\\.|[^\]])*\]', content):
            content = re.sub(r'PB\[(?:\\.|[^\]])*\]', f'PB[{black_id}]', content)
        else:
            content = re.sub(r'\(\s*;', f'(;PB[{black_id}]', content, count=1)

        # Replace PW if exists, else inject into root node
        if re.search(r'PW\[(?:\\.|[^\]])*\]', content):
            content = re.sub(r'PW\[(?:\\.|[^\]])*\]', f'PW[{white_id}]', content)
        else:
            content = re.sub(r'\(\s*;', f'(;PW[{white_id}]', content, count=1)

        return content

    @classmethod
    def get_game_sgf_content(cls, game: Game) -> Optional[str]:
        """
        Retrieves raw SGF content from game.sgf file on disk.
        Pure read-only operation: does not fetch or mutate database/filesystem.
        """
        if game.sgf:
            try:
                with game.sgf.open("r") as f:
                    content = f.read()
                    if isinstance(content, bytes):
                        return content.decode("utf-8", errors="replace")
                    return content
            except Exception as e:
                logger.warning(f"Error reading SGF for game {game.id}: {e}")

        return None

    @classmethod
    def generate_report(cls, season: Season) -> dict:
        """
        Compiles the report payload for the given season:
        {
            "total_players": int,
            "total_games": int,
            "players": { "<egd_id_or_nick>": "<name>" },
            "sgfs": [ "<sgf_with_player_ids>", ... ]
        }
        """
        games = (
            Game.objects.filter(
                group__season=season,
                win_type__in=[WinType.POINTS, WinType.RESIGN, WinType.TIME],
            )
            .exclude(sgf="")
            .exclude(sgf__isnull=True)
            .select_related("black__player", "white__player", "group__season")
            .order_by("round__number", "id")
        )

        players = {}
        sgfs = []

        for game in games:
            if not game.black or not game.black.player or not game.white or not game.white.player:
                continue

            bp = game.black.player
            wp = game.white.player

            b_id = cls.get_player_identifier(bp)
            w_id = cls.get_player_identifier(wp)

            raw_content = cls.get_game_sgf_content(game)
            if not raw_content:
                continue

            for p, p_id in [(bp, b_id), (wp, w_id)]:
                if p_id not in players:
                    full_name = f"{p.first_name} {p.last_name}".strip()
                    players[p_id] = full_name if full_name else p.nick

            transformed_sgf = cls.transform_sgf(raw_content, b_id, w_id)
            sgfs.append(transformed_sgf)

        return {
            "total_players": len(players),
            "total_games": len(sgfs),
            "players": players,
            "sgfs": sgfs,
        }

    # Backward compatibility alias
    generate_raport = generate_report


SeasonRaportService = SeasonReportService
