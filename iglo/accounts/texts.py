from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

mark_safe_lazy = lazy(mark_safe, str)

EMAIL_HELP_TEXT = _("Twój adres e-mail będzie widoczny dla administratorów ligi oraz dla Twoich przeciwników. Będziesz używać go do logowania oraz bedziemy przesyłać na niego powiadomienia.")
FIRST_NAME_HELP_TEXT = _("Twoje imię będzie widoczne dla administratorów ligi oraz Twoich przeciwników.")
LAST_NAME_HELP_TEXT = _("Twoje nazwisko będzie widoczne dla administratorów ligi oraz Twoich przeciwników.")
PASSWORD_LABEL = _("Hasło")
OLD_PASSWORD_LABEL = _("Stare hasło")
NEW_PASSWORD_LABEL = _("Nowe hasło")
NEW_EMAIL_LABEL = _("Nowy email")
CONFIRM_NEW_PASSWORD_LABEL = _("Powtórz nowe hasło")
PASSWORD_MISMATCH_ERROR = _("Nowe hasło nie zostało powtórzone poprawnie")
PASSWORD_INCORRECT_ERROR = _("Hasło jest niepoprawne")
NICK_HELP_TEXT = _("Pod tą nazwą będziesz widoczny jako gracz w lidze.")
RANK_HELP_TEXT = mark_safe_lazy(_('Twoja aktualna siła w <a href="#" data-bs-toggle="modal" data-bs-target="#gor-modal">punktach GoR</a>. Jeżeli dopiero zaczynasz przygodę z Go wpisz 100.'))
EMAIL_ERROR = _("Ten e-mail jest już zajęty.")
NICK_ERROR = _("Ten nick jest już zajęty.")
REGISTRATION_SUCCESS = _("Konto zostało utworzone. Możesz się zalogować.")
PASSWORD_HELP_TEXT = _("Wybierz trudne hasło składające się z co najmniej 8 znaków.")
FIRST_NAME_LABEL = _("Imie")
LAST_NAME_LABEL = _("Nazwisko")
AGREEMENT_HELP_LABEL = mark_safe_lazy(_("Zapoznałem się i zgadzam się z <a href='/rules'>regulaminem ligi</a>"))
PASSWORD_AND_OR_EMAIL_CHANGE_SUCCESS = _("Hasło i/lub email zostały zmienione")
ROLE_REFEREE = _("Sędzia")
ROLE_TEACHER = _("Nauczyciel")
