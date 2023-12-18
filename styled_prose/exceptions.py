class BadConfigException(ValueError):
    """Raised when an invalid config, likely an invalid TOML, is read."""


class BadStyleException(ValueError):
    """Raised when an invalid paragraph style is encountered during validation."""


class BadFontException(ValueError):
    """
    Raised when trying to parse an invalid font family is encountered during validation.
    """
