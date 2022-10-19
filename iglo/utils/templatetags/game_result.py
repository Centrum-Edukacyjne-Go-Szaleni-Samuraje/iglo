from django.template.defaultfilters import register

from league.models import WinType, Game


@register.filter
def result(game: Game):
    if not game.is_played:
        return None
    if not game.winner or game.is_bye:
        return WinType(game.win_type).label
    winner_color = "B" if game.winner == game.black else "W"
    if game.win_type:
        win_type = (
            game.points_difference or 0.5 if game.win_type == WinType.POINTS else WinType(game.win_type).label
        )
        return f"{winner_color}+{win_type}"
    return winner_color
