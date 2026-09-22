"""Exceptions."""


class GuruError(Exception):
    """Base."""


class GuruHTTPError(GuruError):
    pass


class GuruParseError(GuruError):
    pass


class GuruNotFoundError(GuruError):
    pass
