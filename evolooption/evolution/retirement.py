"""Retirement boundary for the frozen evolooption framework."""


class RetiredFrameworkError(RuntimeError):
    """Raised when an unavailable framework mutation path is requested."""


__all__ = ["RetiredFrameworkError"]
