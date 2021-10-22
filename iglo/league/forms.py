from django import forms


class PrepareSeasonForm(forms.Form):
    start_date = forms.DateField(label="Data rozpoczęcia")
    players_per_group = forms.IntegerField(label="Liczba graczy w grupie")
    promotion_count = forms.IntegerField(label="Liczba graczy awansowanych")
