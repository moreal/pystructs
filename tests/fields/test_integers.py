"""Tests for integer field types."""

import pytest

from pystructs import (
    Int8,
    Int16,
    Int32,
    Int64,
    Struct,
    UInt8,
    UInt16,
    UInt32,
    UInt64,
)
from pystructs.exceptions import UnexpectedEOF


class TestInt8:
    """Tests for Int8 field."""

    def test_parse_positive(self):
        """Parse positive Int8 value."""

        class S(Struct):
            value = Int8()

        s = S.parse(bytes([0x7F]))
        assert s.value == 127

    def test_parse_negative(self):
        """Parse negative Int8 value."""

        class S(Struct):
            value = Int8()

        s = S.parse(bytes([0xFF]))
        assert s.value == -1

    def test_serialize(self):
        """Serialize Int8 value."""

        class S(Struct):
            value = Int8()

        s = S(value=-1)
        assert s.to_bytes() == bytes([0xFF])


class TestUInt8:
    """Tests for UInt8 field."""

    def test_parse(self):
        """Parse UInt8 value."""

        class S(Struct):
            value = UInt8()

        s = S.parse(bytes([0xFF]))
        assert s.value == 255

    def test_serialize(self):
        """Serialize UInt8 value."""

        class S(Struct):
            value = UInt8()

        s = S(value=255)
        assert s.to_bytes() == bytes([0xFF])


class TestInt16:
    """Tests for Int16 field."""

    def test_parse_little_endian(self):
        """Parse Int16 in little-endian."""

        class S(Struct):
            value = Int16()

        s = S.parse(bytes([0x01, 0x02]))
        assert s.value == 0x0201

    def test_parse_big_endian(self):
        """Parse Int16 in big-endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Int16()

        s = S.parse(bytes([0x01, 0x02]))
        assert s.value == 0x0102

    def test_parse_negative(self):
        """Parse negative Int16 value."""

        class S(Struct):
            value = Int16()

        s = S.parse(bytes([0xFF, 0xFF]))
        assert s.value == -1

    def test_serialize_little_endian(self):
        """Serialize Int16 in little-endian."""

        class S(Struct):
            value = Int16()

        s = S(value=0x0201)
        assert s.to_bytes() == bytes([0x01, 0x02])

    def test_serialize_big_endian(self):
        """Serialize Int16 in big-endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Int16()

        s = S(value=0x0102)
        assert s.to_bytes() == bytes([0x01, 0x02])


class TestUInt16:
    """Tests for UInt16 field."""

    def test_parse_little_endian(self):
        """Parse UInt16 in little-endian."""

        class S(Struct):
            value = UInt16()

        s = S.parse(bytes([0xFF, 0xFF]))
        assert s.value == 65535

    def test_parse_big_endian(self):
        """Parse UInt16 in big-endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = UInt16()

        s = S.parse(bytes([0xFF, 0xFF]))
        assert s.value == 65535


class TestInt32:
    """Tests for Int32 field."""

    def test_parse_little_endian(self):
        """Parse Int32 in little-endian."""

        class S(Struct):
            value = Int32()

        s = S.parse(bytes([0x01, 0x02, 0x03, 0x04]))
        assert s.value == 0x04030201

    def test_parse_big_endian(self):
        """Parse Int32 in big-endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Int32()

        s = S.parse(bytes([0x01, 0x02, 0x03, 0x04]))
        assert s.value == 0x01020304

    def test_parse_negative(self):
        """Parse negative Int32 value."""

        class S(Struct):
            value = Int32()

        s = S.parse(bytes([0xFF, 0xFF, 0xFF, 0xFF]))
        assert s.value == -1


class TestUInt32:
    """Tests for UInt32 field."""

    def test_parse_max_value(self):
        """Parse maximum UInt32 value."""

        class S(Struct):
            value = UInt32()

        s = S.parse(bytes([0xFF, 0xFF, 0xFF, 0xFF]))
        assert s.value == 0xFFFFFFFF


class TestInt64:
    """Tests for Int64 field."""

    def test_parse_little_endian(self):
        """Parse Int64 in little-endian."""

        class S(Struct):
            value = Int64()

        data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        s = S.parse(data)
        assert s.value == 0x0807060504030201

    def test_parse_negative(self):
        """Parse negative Int64 value."""

        class S(Struct):
            value = Int64()

        s = S.parse(bytes([0xFF] * 8))
        assert s.value == -1


class TestUInt64:
    """Tests for UInt64 field."""

    def test_parse_max_value(self):
        """Parse maximum UInt64 value."""

        class S(Struct):
            value = UInt64()

        s = S.parse(bytes([0xFF] * 8))
        assert s.value == 0xFFFFFFFFFFFFFFFF


class TestFieldLevelEndian:
    """Tests for field-level endian override."""

    def test_field_endian_overrides_struct(self):
        """Field-level endian takes precedence over struct-level."""

        class S(Struct):
            class Meta:
                endian = "little"

            little_val = UInt16()
            big_val = UInt16(endian="big")

        s = S.parse(bytes([0x01, 0x02, 0x01, 0x02]))
        assert s.little_val == 0x0201  # little-endian
        assert s.big_val == 0x0102  # big-endian

    def test_field_endian_in_serialization(self):
        """Field-level endian works in serialization."""

        class S(Struct):
            class Meta:
                endian = "little"

            little_val = UInt16()
            big_val = UInt16(endian="big")

        s = S(little_val=0x0201, big_val=0x0102)
        data = s.to_bytes()
        assert data == bytes([0x01, 0x02, 0x01, 0x02])


class TestIntegerErrors:
    """Tests for integer field error handling."""

    def test_unexpected_eof(self):
        """UnexpectedEOF raised when data is too short."""

        class S(Struct):
            value = UInt32()

        with pytest.raises(UnexpectedEOF) as exc_info:
            S.parse(bytes([0x01, 0x02]))

        assert exc_info.value.expected == 4
        assert exc_info.value.got == 2


class TestIntegerDefaults:
    """Tests for integer field defaults."""

    def test_default_value(self):
        """Default value is used when not provided."""

        class S(Struct):
            value = UInt32(default=0xDEADBEEF)

        s = S()
        assert s.value == 0xDEADBEEF

    def test_default_zero(self):
        """Default value of 0 works correctly."""

        class S(Struct):
            value = UInt32(default=0)

        s = S()
        assert s.value == 0
        assert s.to_bytes() == bytes([0, 0, 0, 0])
