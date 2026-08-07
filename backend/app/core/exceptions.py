"""Application-level exceptions.

Each carries its own HTTP status code so the API layer never has to guess
what a given failure should return — raise the right exception, the
handler in main.py takes care of the response shape.
"""


class AppError(Exception):
    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404


class InvalidCredentialsError(AppError):
    status_code = 401


class DuplicateEmailError(AppError):
    status_code = 409


class UnsupportedUploadError(AppError):
    status_code = 400


class StorageUnavailableError(AppError):
    status_code = 502
