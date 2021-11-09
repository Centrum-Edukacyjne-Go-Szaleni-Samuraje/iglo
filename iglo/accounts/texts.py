from django.utils.safestring import mark_safe

EMAIL_HELP_TEXT = "Twój adres e-mail będzie widoczny tylko dla administratorów ligi. Będziesz używać go do logowania oraz bedziemy przesyłać na niego powiadomienia."
PASSWORD_LABEL = "Hasło"
NICK_HELP_TEXT = "Pod tą nazwą będziesz widoczny dla innych graczy."
RANK_HELP_TEXT = mark_safe('Twoja aktualna siła w <a href="#" data-bs-toggle="modal" data-bs-target="#gor-modal">punktach GoR</a>. Jeżeli dopiero zaczynasz przygodę z Go wpisz 100.')
EMAIL_ERROR = "Ten e-mail jest już zajęty."
NICK_ERROR = "Ten nick jest już zajęty."
REGISTRATION_SUCCESS = "Konto zostało utworzone. Możesz się zalogować."
PASSWORD_HELP_TEXT = "Wybierz trudne hasło oraz składające się z conajmniej 8 znaków."
FIRST_NAME_LABEL = "Imie"
LAST_NAME_LABEL = "Nazwisko"
