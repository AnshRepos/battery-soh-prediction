"""Tests for core/custom_exceptions.py — ETM exception hierarchy."""

import pytest
from core.custom_exceptions import (
    APIRequestError,
    AuthenticationError,
    ConfigurationError,
    ETMBaseException,
    ResourceNotFoundError,
    XMLParseError,
)


class TestETMBaseException:
    """Tests for the base exception class."""

    def test_stores_message(self):
        exc = ETMBaseException("something broke")
        assert exc.message == "something broke"

    def test_stores_error_code(self):
        exc = ETMBaseException("msg", error_code="E001")
        assert exc.error_code == "E001"

    def test_stores_details(self):
        details = {"resource": "testcase", "id": "123"}
        exc = ETMBaseException("msg", details=details)
        assert exc.details == details

    def test_details_defaults_to_empty_dict(self):
        exc = ETMBaseException("msg")
        assert exc.details == {}

    def test_str_without_error_code(self):
        exc = ETMBaseException("plain message")
        assert str(exc) == "plain message"

    def test_str_with_error_code(self):
        exc = ETMBaseException("coded message", error_code="E042")
        assert str(exc) == "[E042] coded message"

    def test_inherits_from_exception(self):
        assert issubclass(ETMBaseException, Exception)


_CHILD_EXCEPTIONS = [
    AuthenticationError,
    ResourceNotFoundError,
    APIRequestError,
    XMLParseError,
    ConfigurationError,
]


class TestChildExceptions:
    """Verify each child exception inherits from ETMBaseException and is raisable."""

    @pytest.mark.parametrize("exc_cls", _CHILD_EXCEPTIONS, ids=lambda c: c.__name__)
    def test_inherits_from_base(self, exc_cls):
        assert issubclass(exc_cls, ETMBaseException)

    @pytest.mark.parametrize("exc_cls", _CHILD_EXCEPTIONS, ids=lambda c: c.__name__)
    def test_can_be_raised_and_caught(self, exc_cls):
        with pytest.raises(ETMBaseException):
            raise exc_cls("test error")

    @pytest.mark.parametrize("exc_cls", _CHILD_EXCEPTIONS, ids=lambda c: c.__name__)
    def test_preserves_message(self, exc_cls):
        exc = exc_cls("detail", error_code="X1", details={"k": "v"})
        assert exc.message == "detail"
        assert exc.error_code == "X1"
        assert exc.details == {"k": "v"}
