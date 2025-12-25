class ADGException(Exception):
    pass


class GameNotFoundError(ADGException):
    pass


class TeamNotFoundError(ADGException):
    pass


class GameNotRunningError(ADGException):
    pass


class InvalidFlagError(ADGException):
    pass


class DuplicateFlagError(ADGException):
    pass


class ExpiredFlagError(ADGException):
    pass


class OwnFlagError(ADGException):
    pass


class CheckerError(ADGException):
    pass


class DockerError(ADGException):
    pass
