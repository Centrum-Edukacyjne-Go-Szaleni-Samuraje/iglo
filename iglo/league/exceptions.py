from utils.exceptions import BusinessError


class CanNotRescheduleGameError(BusinessError):
    pass


class WrongRescheduleDateError(BusinessError):
    pass
