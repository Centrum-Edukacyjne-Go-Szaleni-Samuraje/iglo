from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

OGS_USERNAME_LABEL = "Konto OGS"
KGS_USERNAME_LABEL = "Konto KGS"
RANK_LABEL = "Ranking"
EGD_PIN_LABEL = "Pin EGD"
EGD_APPROVAL_LABEL = "Chce raportować moje gry do EGD"
AVAILABILITY_LABEL = "Dostępność"
COUNTRY_LABEL = "Kraj"
CLUB_LABEL = "Klub"
RANK_HELP_TEXT = "W punktach GoR."
EGD_HELP_TEXT = mark_safe("Jeżeli posiadasz konto w EGD Twój pin znajdziesz na stronie swojego profilu. Aby znaleźć swój profil EGD użyj <a href='https://www.europeangodatabase.eu/EGD/Find_Player.php' target='blank'>wyszukiwarki</a>.")
EGD_APPROVAL_HELP_TEXT = "Jeżeli wszyscy gracze w Twojej grupie wyrażą zgodę, to gry z danej grupy będą raportowanie do EGD."
AVAILABILITY_HELP_TEXT = "Twoja dostępność czasowa dot. rozgrywania gier. Informacja ta będzie dostępna dla Twoich przeciwników wraz z Twoimi danymi kontaktowymi. Ma ona na celu usprawnić umawianie terminu rozgrywki. Przykład: \"Mogę grać tylko po 18:00, od 24.12 do 27.12 jestem niedostępny\". "
CLUB_HELP_TEXT = "4 literowe oznaczenie klubu/miasta używane w EGD"
NICK_ERROR = "Ten nick jest już zajęty."
PLAYER_UPDATE_SUCCESS = "Twoje dane zostały zmienione."
MISSING_PLAYER_ERROR = "Gracz o podanym nicku nie istnieje."
WINNER_LABEL = "Zwycięzca"
DATE_LABEL = "Termin gry"
WIN_TYPE_LABEL = "Typ zwycięstwa"
POINTS_DIFFERENCE_LABEL = "Różnica punktów"
SGF_LABEL = "SGF"
SGF_HELP_TEXT = "Nie musisz uzupełniać pliku SGF jeżeli gra odbyła się na OGS. W innym przypadku prosimy o wgranie pliku z grą."
LINK_LABEL = "Link do gry na OGS"
START_DATE_LABEL = "Data rozpoczęcia"
PLAYERS_PER_GROUP_LABEL = "Liczba graczy w grupie"
PROMOTION_COUNT_LABEL = "Liczba graczy awansujących/spadających"
WIN_TYPE_POINTS = "Punkty"
WIN_TYPE_RESIGN = "Rezygnacja"
WIN_TYPE_TIME = "Czas"
WIN_TYPE_BYE = "Bye"
WIN_TYPE_NOT_PLAYED = "Nierozegrana"
WINNER_REQUIRED_ERROR = "To pole jest wymagane przy wybranym typie zwycięstwa."
WIN_TYPE_REQUIRED_ERROR = "To pole jest wymagane gdy wybrany jest zwycięzca."
POINTS_DIFFERENCE_REQUIRED_ERROR = "To pole jest wymagane przy wybranym typie zwycięstwa."
POINTS_DIFFERENCE_HALF_POINT_ERROR = "Wartość musi być zakończona 0,5 punkta."
POINTS_DIFFERENCE_NEGATIVE_ERROR = "Wartość musi być większa od 0."
SGF_OR_LINK_REQUIRED_ERROR = "Uzupełnij plik SGF lub link do gry na OGS."
AUTO_JOIN_LABEL = "Dołącz Automatycznie"
AUTO_JOIN_HELP_TEXT = "Jeżeli to pole jest zaznaczone zostaniesz automatycznie dołączona/y do następnego sezonu."
FIRST_NAME_LABEL = "Imie"
LAST_NAME_LABEL = "Nazwisko"
SEASON_STATE_DRAFT = "W przygotowaniu"
SEASON_STATE_IN_PROGRES = "Trwa"
SEASON_STATE_FINISHED = "Zakończony"
PREVIOUS_SEASON_NOT_CLOSED_ERROR = "Poprzedni sezon nie został zamknięty."
GAMES_WITHOUT_RESULT_ERROR = "Nie wszystkie gry zostały rozegrane."
OGS_GAME_LINK_ERROR = "To nie jest poprawny link do gry OGS - format linku to: https://online-go.com/game/<NUMER_GRY>"
AI_ANALYSE_LINK_HELP_TEXT = "Pole zostanie wypełnione automatycznie jeżeli pozostawisz je puste."
UPDATE_GOR_MESSAGE = "Ranking są aktualizowane. O zakończeniu procesu zostaniesz poinformowany emailem."
UPDATE_GOR_MAIL_SUBJECT = "Aktualizacja GOR"
UPDATE_GOR_MAIL_CONTENT = "Aktualizacja rankingów graczy została zakończona"
MEMBER_WITHDRAW_SUCCESS = _("Gracz został wycofany z aktualnego sezonu.")
ALREADY_PLAYED_GAMES_ERROR = _("Gracz już rozegrał gry w akutlanym sezonie. Wycofanie jest niemożliwe.")
