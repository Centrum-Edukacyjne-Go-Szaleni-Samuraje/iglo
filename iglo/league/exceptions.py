from league import texts
from utils.exceptions import BusinessError


class CanNotRescheduleGameError(BusinessError):
    message = texts.CAN_NOT_RESCHEDULE_ERROR


class WrongRescheduleDateError(BusinessError):
    message = texts.WRONG_RESCHEDULE_DATE_ERROR


class WrongSeasonStateError(BusinessError):
    message = texts.WRONG_SEASON_STATE_ERROR


class GamesWithoutResultError(BusinessError):
    message = texts.GAMES_WITHOUT_RESULT_ERROR


class CanNotReportGameResultError(BusinessError):
    message = texts.CAN_NOT_REPORT_GAME_RESULT_ERROR


class AlreadyPlayedGamesError(BusinessError):
    message = texts.ALREADY_PLAYED_GAMES_ERROR
