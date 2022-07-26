from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

mark_safe_lazy = lazy(mark_safe, str)

OGS_USERNAME_LABEL = _("Konto OGS")
KGS_USERNAME_LABEL = _("Konto KGS")
RANK_LABEL = _("Ranking")
EGD_PIN_LABEL = _("Pin EGD")
EGD_APPROVAL_LABEL = _("Chce raportować moje gry do EGD")
AVAILABILITY_LABEL = _("Dostępność")
COUNTRY_LABEL = _("Kraj")
CLUB_LABEL = _("Klub")
RANK_HELP_TEXT = _("W punktach GoR.")
EGD_HELP_TEXT = mark_safe_lazy(_("Jeżeli posiadasz konto w EGD Twój pin znajdziesz na stronie swojego profilu. Aby znaleźć swój profil EGD użyj <a href='https://www.europeangodatabase.eu/EGD/Find_Player.php' target='blank'>wyszukiwarki</a>."))
EGD_APPROVAL_HELP_TEXT = _("Jeżeli wszyscy gracze w Twojej grupie wyrażą zgodę, to gry z danej grupy będą raportowanie do EGD.")
AVAILABILITY_HELP_TEXT = _("Twoja dostępność czasowa dot. rozgrywania gier. Informacja ta będzie dostępna dla Twoich przeciwników wraz z Twoimi danymi kontaktowymi. Ma ona na celu usprawnić umawianie terminu rozgrywki. Przykład: \"Mogę grać tylko po 18:00, od 24.12 do 27.12 jestem niedostępny\". ")
CLUB_HELP_TEXT = _("4 literowe oznaczenie klubu/miasta używane w EGD")
NICK_ERROR = _("Ten nick jest już zajęty.")
PLAYER_UPDATE_SUCCESS = _("Twoje dane zostały zmienione.")
MISSING_PLAYER_ERROR = _("Gracz o podanym nicku nie istnieje.")
WINNER_LABEL = _("Zwycięzca")
DATE_LABEL = _("Termin gry")
WIN_TYPE_LABEL = _("Typ zwycięstwa")
POINTS_DIFFERENCE_LABEL = _("Różnica punktów")
SGF_LABEL = _("SGF")
SGF_HELP_TEXT = _("Nie musisz uzupełniać pliku SGF jeżeli gra odbyła się na OGS. W innym przypadku prosimy o wgranie pliku z grą.")
LINK_LABEL = _("Link do gry na OGS")
START_DATE_LABEL = _("Data rozpoczęcia")
PLAYERS_PER_GROUP_LABEL = _("Liczba graczy w grupie")
PROMOTION_COUNT_LABEL = _("Liczba graczy awansujących/spadających")
WIN_TYPE_POINTS = _("Punkty")
WIN_TYPE_RESIGN = _("Rezygnacja")
WIN_TYPE_TIME = _("Czas")
WIN_TYPE_BYE = _("Bye")
WIN_TYPE_NOT_PLAYED = _("Nierozegrana")
WINNER_REQUIRED_ERROR = _("To pole jest wymagane przy wybranym typie zwycięstwa.")
WIN_TYPE_REQUIRED_ERROR = _("To pole jest wymagane gdy wybrany jest zwycięzca.")
POINTS_DIFFERENCE_REQUIRED_ERROR = _("To pole jest wymagane przy wybranym typie zwycięstwa.")
POINTS_DIFFERENCE_HALF_POINT_ERROR = _("Wartość musi być zakończona 0,5 punkta.")
POINTS_DIFFERENCE_NEGATIVE_ERROR = _("Wartość musi być większa od 0.")
SGF_OR_LINK_REQUIRED_ERROR = _("Uzupełnij plik SGF lub link do gry na OGS.")
AUTO_JOIN_LABEL = _("Dołącz Automatycznie")
AUTO_JOIN_HELP_TEXT = _("Jeżeli to pole jest zaznaczone zostaniesz automatycznie dołączona/y do następnego sezonu.")
FIRST_NAME_LABEL = _("Imię")
LAST_NAME_LABEL = _("Nazwisko")
SEASON_STATE_DRAFT = _("W przygotowaniu")
SEASON_STATE_IN_PROGRES = _("Trwa")
SEASON_STATE_FINISHED = _("Zakończony")
PREVIOUS_SEASON_NOT_CLOSED_ERROR = _("Poprzedni sezon nie został zamknięty.")
GAMES_WITHOUT_RESULT_ERROR = _("Nie wszystkie gry zostały rozegrane.")
OGS_GAME_LINK_ERROR = _("To nie jest poprawny link do gry OGS - format linku to: https://online-go.com/game/<NUMER_GRY>")
AI_ANALYSE_LINK_HELP_TEXT = _("Pole zostanie wypełnione automatycznie jeżeli pozostawisz je puste.")
UPDATE_GOR_MESSAGE = _("Ranking są aktualizowane. O zakończeniu procesu zostaniesz poinformowany emailem.")
UPDATE_GOR_MAIL_SUBJECT = _("Aktualizacja GOR")
UPDATE_GOR_MAIL_CONTENT = _("Aktualizacja rankingów graczy została zakończona")
MEMBER_WITHDRAW_SUCCESS = _("Gracz został wycofany z aktualnego sezonu.")
ALREADY_PLAYED_GAMES_ERROR = _("Gracz już rozegrał gry w akutlanym sezonie. Wycofanie jest niemożliwe.")
CAN_NOT_RESCHEDULE_ERROR = _("Nie można zmienić terminu gry.")
WRONG_RESCHEDULE_DATE_ERROR = _("Gra nie może zostać zaplanowana w podanym terminie.")
GAME_RESCHEDULED_SUCCESS = _("Termin gry został zmieniony.")
