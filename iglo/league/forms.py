from django import forms

from league.models import Player


class PlayerSettingsForm(forms.Form):
    nick = forms.SlugField(required=False)
    rank = forms.CharField(required=False)
    nick_ogs = forms.CharField(required=False)
    nick_kgs = forms.CharField(required=False)

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Player.objects.filter(nick=nick).exists():
            raise forms.ValidationError("Ten nick jest już zajęty.")
        return nick
