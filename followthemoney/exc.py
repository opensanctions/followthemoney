from typing import TypedDict


class ErrorSpec(TypedDict, total=False):
    properties: dict[str, str]


class FollowTheMoneyException(Exception):
    """Catch-all exception for errors emitted by this library."""


class MetadataException(FollowTheMoneyException):
    """An exception raised by dataset metadata validation."""


class InvalidData(FollowTheMoneyException):
    """Schema validation errors will be caught by the API."""

    def __init__(self, message: str, errors: ErrorSpec | None = None) -> None:
        super().__init__(message)
        self.errors: ErrorSpec = errors or {}


class InvalidModel(FollowTheMoneyException):
    """The schema model is not defined correctly."""


class InvalidMapping(FollowTheMoneyException):
    """A data mapping was invalid."""


class InvalidDatasetQuery(FollowTheMoneyException):
    """A dataset query DSL expression was invalid."""
