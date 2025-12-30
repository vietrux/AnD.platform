from fastapi import HTTPException


class ADGException(Exception):
    pass


class APIError(ADGException):
    status_code: int = 500
    detail: str = "An error occurred"
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=self.detail)


class GameNotFoundError(APIError):
    status_code = 404
    detail = "Game not found"


class TeamNotFoundError(APIError):
    status_code = 404
    detail = "Team not found"


class TickNotFoundError(APIError):
    status_code = 404
    detail = "Tick not found"


class FlagNotFoundError(APIError):
    status_code = 404
    detail = "Flag not found"


class SubmissionNotFoundError(APIError):
    status_code = 404
    detail = "Submission not found"


class ServiceStatusNotFoundError(APIError):
    status_code = 404
    detail = "Service status not found"


class ScoreboardNotFoundError(APIError):
    status_code = 404
    detail = "Scoreboard not found"


class GameNotRunningError(APIError):
    status_code = 400
    detail = "Game is not running"


class CannotDeleteRunningGameError(APIError):
    status_code = 400
    detail = "Cannot delete a running game. Stop the game first."


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
