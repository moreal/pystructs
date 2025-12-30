"""Exception hierarchy for pystructs."""

from __future__ import annotations

from typing import Any, List

__all__ = (
    "PyStructError",
    "ParseError",
    "UnexpectedEOF",
    "TrailingDataError",
    "ValidationError",
    "FieldValidationError",
    "InconsistencyError",
    "ValidationErrors",
    "SerializationError",
    "StructDefinitionError",
)


class PyStructError(Exception):
    """Base exception for all pystructs errors."""

    pass


class ParseError(PyStructError):
    """Error during parsing binary data."""

    pass


class UnexpectedEOF(ParseError):
    """Unexpected end of data while parsing."""

    def __init__(self, expected: int, got: int, field: str | None = None):
        self.expected = expected
        self.got = got
        self.field = field

        msg = f"Expected {expected} bytes, got {got}"
        if field:
            msg = f"Field '{field}': {msg}"
        super().__init__(msg)


class TrailingDataError(ParseError):
    """Data remains after parsing is complete."""

    def __init__(self, count: int):
        self.count = count
        super().__init__(f"{count} bytes remaining after parsing")


class ValidationError(PyStructError):
    """Validation failed."""

    pass


class FieldValidationError(ValidationError):
    """Field-level validation failed."""

    def __init__(self, field: str, reason: str | Exception):
        self.field = field
        self.reason = reason
        super().__init__(f"Field '{field}': {reason}")


class InconsistencyError(ValidationError):
    """Field value is inconsistent with expected value."""

    def __init__(self, field: str, actual: Any, expected: Any):
        self.field = field
        self.actual = actual
        self.expected = expected
        super().__init__(f"Field '{field}': expected {expected}, got {actual}")


class ValidationErrors(ValidationError):
    """Multiple validation errors occurred."""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        messages = [str(e) for e in errors]
        super().__init__("Multiple validation errors:\n" + "\n".join(messages))


class SerializationError(PyStructError):
    """Error during serialization."""

    def __init__(self, field: str | None = None, reason: str = ""):
        self.field = field
        self.reason = reason
        if field:
            msg = f"Cannot serialize '{field}': {reason}"
        else:
            msg = reason
        super().__init__(msg)


class StructDefinitionError(PyStructError):
    """Error in struct class definition."""

    pass
