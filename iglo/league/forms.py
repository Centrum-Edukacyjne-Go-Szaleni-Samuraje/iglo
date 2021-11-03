from django import forms

from league import texts
from league.models import Game, Member, Player


class PrepareSeasonForm(forms.Form):
    start_date = forms.DateField(label=texts.START_DATE_LABEL)
    players_per_group = forms.IntegerField(label=texts.PLAYERS_PER_GROUP_LABEL)
    promotion_count = forms.IntegerField(label=texts.PROMOTION_COUNT_LABEL)


class GameResultUpdateForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            "winner",
            "win_type",
            "points_difference",
            "link",
            "sgf",
        ]
        labels = {
            "winner": texts.WINNER_LABEL,
            "win_type": texts.WIN_TYPE_LABEL,
            "points_difference": texts.POINTS_DIFFERENCE_LABEL,
            "sgf": texts.SGF_LABEL,
            "link": texts.LINK_LABEL,
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["winner"].queryset = Member.objects.filter(id__in=[self.instance.black.id, self.instance.white.id])


class PlayerUpdateForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            "nick",
            "rank",
            "ogs_username",
            "kgs_username",
        ]
        labels = {
            "rank": texts.RANK_LABEL,
            "ogs_username": texts.OGS_USERNAME_LABEL,
            "kgs_username": texts.KGS_USERNAME_LABEL,
        }
        help_texts = {
            "rank": texts.RANK_HELP_TEXT,
        }

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Player.objects.filter(nick__iexact=nick).exists():
            raise forms.ValidationError(texts.NICK_ERROR)
        return nick
