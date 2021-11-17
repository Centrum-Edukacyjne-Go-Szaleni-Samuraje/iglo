from django import forms

from league import texts
from league.models import Game, Member, Player, WinType


class PrepareSeasonForm(forms.Form):
    start_date = forms.DateField(label=texts.START_DATE_LABEL)
    players_per_group = forms.IntegerField(label=texts.PLAYERS_PER_GROUP_LABEL)
    promotion_count = forms.IntegerField(label=texts.PROMOTION_COUNT_LABEL)


class GameResultUpdateForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            "date",
            "winner",
            "win_type",
            "points_difference",
            "link",
            "sgf",
        ]
        labels = {
            "date": texts.DATE_LABEL,
            "winner": texts.WINNER_LABEL,
            "win_type": texts.WIN_TYPE_LABEL,
            "points_difference": texts.POINTS_DIFFERENCE_LABEL,
            "sgf": texts.SGF_LABEL,
            "link": texts.LINK_LABEL,
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["winner"].queryset = Member.objects.filter(id__in=[self.instance.black.id, self.instance.white.id])
        self.fields["win_type"].choices = (wt for wt in WinType.choices if wt[0] != WinType.BYE.value)

    def clean(self):
        cleaned_data = super().clean()
        win_type = cleaned_data["win_type"]
        winner = cleaned_data["winner"]
        if win_type and win_type != WinType.NOT_PLAYED and not winner:
            self.add_error(field="winner", error=texts.WINNER_REQUIRED_ERROR)
        return cleaned_data


class PlayerUpdateForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            "nick",
            "first_name",
            "last_name",
            "rank",
            "ogs_username",
            "kgs_username",
            "auto_join",
        ]
        labels = {
            "first_name": texts.FIRST_NAME_LABEL,
            "last_name": texts.LAST_NAME_LABEL,
            "ogs_username": texts.OGS_USERNAME_LABEL,
            "kgs_username": texts.KGS_USERNAME_LABEL,
            "auto_join": texts.AUTO_JOIN_LABEL,
        }
        help_texts = {
            "rank": texts.RANK_HELP_TEXT,
            "auto_join": texts.AUTO_JOIN_HELP_TEXT,
        }

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Player.objects.exclude(id=self.instance.id).filter(nick__iexact=nick).exists():
            raise forms.ValidationError(texts.NICK_ERROR)
        return nick
