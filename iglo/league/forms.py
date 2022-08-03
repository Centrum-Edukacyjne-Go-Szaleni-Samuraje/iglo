import re

from django import forms
from django.conf import settings
from django.db.models import BLANK_CHOICE_DASH

from league import texts
from league.models import Member, Player, WinType


class PrepareSeasonForm(forms.Form):
    start_date = forms.DateField(label=texts.START_DATE_LABEL)
    players_per_group = forms.IntegerField(label=texts.PLAYERS_PER_GROUP_LABEL)
    promotion_count = forms.IntegerField(label=texts.PROMOTION_COUNT_LABEL)


def ogs_game_link_validator(value: str) -> None:
    if not re.match(settings.OGS_GAME_LINK_REGEX, value):
        raise forms.ValidationError(texts.OGS_GAME_LINK_ERROR)


class GameRescheduleForm(forms.Form):
    date = forms.DateTimeField(label=texts.DATE_LABEL)


class GameReportResultForm(forms.Form):
    winner = forms.ModelChoiceField(queryset=Member.objects.all(), label=texts.WINNER_LABEL)
    win_type = forms.ChoiceField(
        choices=BLANK_CHOICE_DASH + [wt for wt in WinType.choices if wt[0] != WinType.BYE.value],
        label=texts.WIN_TYPE_LABEL,
    )
    points_difference = forms.DecimalField(
        widget=forms.NumberInput(attrs={"step": 1, "min": 0.5}), required=False, label=texts.POINTS_DIFFERENCE_LABEL
    )
    link = forms.URLField(validators=[ogs_game_link_validator], required=False, label=texts.LINK_LABEL)
    sgf = forms.FileField(required=False, label=texts.SGF_LABEL, help_text=texts.SGF_HELP_TEXT)

    def __init__(self, game, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["winner"].queryset = self.fields["winner"].queryset.filter(id__in=[game.black.id, game.white.id])

    def clean(self):
        cleaned_data = super().clean()
        win_type = cleaned_data["win_type"]
        winner = cleaned_data["winner"]
        points_difference = cleaned_data["points_difference"]
        if win_type and win_type != WinType.NOT_PLAYED and not winner:
            self.add_error(field="winner", error=texts.WINNER_REQUIRED_ERROR)
        if winner and not win_type:
            self.add_error(field="win_type", error=texts.WIN_TYPE_REQUIRED_ERROR)
        if win_type == WinType.POINTS and not points_difference:
            self.add_error(field="points_difference", error=texts.POINTS_DIFFERENCE_REQUIRED_ERROR)
        if win_type and win_type != WinType.NOT_PLAYED and not (cleaned_data.get("sgf") or cleaned_data.get("link")):
            self.add_error(field=None, error=texts.SGF_OR_LINK_REQUIRED_ERROR)
        return cleaned_data


class GameSubmitReviewForm(forms.Form):
    link = forms.URLField()


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
            "egd_pin",
            "egd_approval",
            "country",
            "club",
            "availability",
        ]
        labels = {
            "first_name": texts.FIRST_NAME_LABEL,
            "last_name": texts.LAST_NAME_LABEL,
            "ogs_username": texts.OGS_USERNAME_LABEL,
            "kgs_username": texts.KGS_USERNAME_LABEL,
            "auto_join": texts.AUTO_JOIN_LABEL,
            "rank": texts.RANK_LABEL,
            "egd_pin": texts.EGD_PIN_LABEL,
            "egd_approval": texts.EGD_APPROVAL_LABEL,
            "availability": texts.AVAILABILITY_LABEL,
            "country": texts.COUNTRY_LABEL,
            "club": texts.CLUB_LABEL,
        }
        help_texts = {
            "rank": texts.RANK_HELP_TEXT,
            "auto_join": texts.AUTO_JOIN_HELP_TEXT,
            "egd_pin": texts.EGD_HELP_TEXT,
            "egd_approval": texts.EGD_APPROVAL_HELP_TEXT,
            "availability": texts.AVAILABILITY_HELP_TEXT,
            "club": texts.CLUB_HELP_TEXT,
        }
        widgets = {
            "availability": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Player.objects.exclude(id=self.instance.id).filter(nick__iexact=nick).exists():
            raise forms.ValidationError(texts.NICK_ERROR)
        return nick
