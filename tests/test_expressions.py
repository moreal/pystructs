"""Tests for the expression system."""

import pytest

from pystructs import Bytes, Struct, UInt8
from pystructs.expressions import Checksum, Const, Len, Value


class TestLen:
    """Tests for Len expression."""

    def test_len_of_bytes(self):
        """Get length of bytes field."""

        class S(Struct):
            data = Bytes(size=5)

        s = S(data=b"Hello")
        expr = Len("data")
        assert expr.evaluate(s) == 5

    def test_len_of_array(self):
        """Get length of array field."""
        from pystructs import Array

        class S(Struct):
            items = Array(UInt8(), count=3, default=[1, 2, 3])

        s = S()
        expr = Len("items")
        assert expr.evaluate(s) == 3


class TestValue:
    """Tests for Value expression."""

    def test_value_of_field(self):
        """Get value of a field."""

        class S(Struct):
            version = UInt8()

        s = S(version=5)
        expr = Value("version")
        assert expr.evaluate(s) == 5


class TestConst:
    """Tests for Const expression."""

    def test_const_value(self):
        """Return constant value."""

        class S(Struct):
            value = UInt8()

        s = S(value=0)
        expr = Const(42)
        assert expr.evaluate(s) == 42


class TestChecksum:
    """Tests for Checksum expression."""

    def test_crc32_checksum(self):
        """Calculate CRC32 checksum."""
        import binascii

        class S(Struct):
            data = Bytes(size=5)

        s = S(data=b"Hello")
        expr = Checksum("data", "crc32")

        expected = binascii.crc32(b"Hello") & 0xFFFFFFFF
        assert expr.evaluate(s) == expected

    def test_unknown_algorithm(self):
        """Raise error for unknown algorithm."""

        class S(Struct):
            data = Bytes(size=5)

        s = S(data=b"Hello")
        expr = Checksum("data", "unknown")

        with pytest.raises(ValueError, match="Unknown checksum algorithm"):
            expr.evaluate(s)


class TestBinaryOp:
    """Tests for BinaryOp expression."""

    def test_add_expressions(self):
        """Add two expressions."""

        class S(Struct):
            a = UInt8()
            b = UInt8()

        s = S(a=10, b=20)
        expr = Value("a") + Value("b")
        assert expr.evaluate(s) == 30

    def test_add_with_constant(self):
        """Add expression and constant."""

        class S(Struct):
            a = UInt8()

        s = S(a=10)
        expr = Value("a") + 5
        assert expr.evaluate(s) == 15

    def test_subtract_expressions(self):
        """Subtract two expressions."""

        class S(Struct):
            a = UInt8()
            b = UInt8()

        s = S(a=20, b=8)
        expr = Value("a") - Value("b")
        assert expr.evaluate(s) == 12

    def test_multiply_expressions(self):
        """Multiply two expressions."""

        class S(Struct):
            a = UInt8()
            b = UInt8()

        s = S(a=5, b=4)
        expr = Value("a") * Value("b")
        assert expr.evaluate(s) == 20

    def test_divide_expressions(self):
        """Divide two expressions."""

        class S(Struct):
            a = UInt8()
            b = UInt8()

        s = S(a=20, b=4)
        expr = Value("a") / Value("b")
        assert expr.evaluate(s) == 5.0

    def test_complex_expression(self):
        """Complex expression with multiple operations."""

        class S(Struct):
            header_len = UInt8()
            payload_len = UInt8()

        s = S(header_len=4, payload_len=10)
        # (header_len + payload_len) * 2
        expr = (Len("header_len") + Value("payload_len")) * Const(2)
        # Note: Len of an int doesn't make sense, use Value instead for this test
        expr = (Value("header_len") + Value("payload_len")) * Const(2)
        assert expr.evaluate(s) == 28

    def test_len_plus_len(self):
        """Add two Len expressions."""

        class S(Struct):
            header = Bytes(size=4)
            payload = Bytes(size=8)

        s = S(header=b"HEAD", payload=b"PAYLOADX")
        expr = Len("header") + Len("payload")
        assert expr.evaluate(s) == 12
