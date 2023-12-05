class BadStyleException(ValueError):
    """Raised when trying to parse an invalid paragraph style."""


class BadFontException(ValueError):
    """Raised when trying to parse an invalid font family."""


class BadConfigException(ValueError):
    """Raised when trying to parse an invalid config."""
