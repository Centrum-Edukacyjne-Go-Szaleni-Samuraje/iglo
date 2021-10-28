from django import forms

from league.models import Game, Member


class PrepareSeasonForm(forms.Form):
    start_date = forms.DateField(label="Data rozpoczęcia")
    players_per_group = forms.IntegerField(label="Liczba graczy w grupie")
    promotion_count = forms.IntegerField(label="Liczba graczy awansowanych")


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
            "winner": "Zwycięzca",
            "win_type": "Typ zwycięstwa",
            "points_difference": "Różnica punktów",
            "sgf": "SGF",
            "link": "Link do gry",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["winner"].queryset = Member.objects.filter(id__in=[self.instance.black.id, self.instance.white.id])
