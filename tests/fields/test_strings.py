"""Tests for string field types."""

import pytest

from pystructs import (
    FixedString,
    NullTerminatedString,
    Ref,
    String,
    Struct,
    UInt8,
)
from pystructs.exceptions import SerializationError


class TestFixedString:
    """Tests for FixedString field."""

    def test_parse_fixed_string(self):
        """Parse fixed-length string."""

        class S(Struct):
            name = FixedString(5)

        s = S.parse(b"Hello")
        assert s.name == "Hello"

    def test_parse_with_padding(self):
        """Parse string with null padding."""

        class S(Struct):
            name = FixedString(8)

        s = S.parse(b"Hi\x00\x00\x00\x00\x00\x00")
        assert s.name == "Hi"

    def test_serialize_with_padding(self):
        """Serialize string with null padding."""

        class S(Struct):
            name = FixedString(8)

        s = S(name="Hi")
        assert s.to_bytes() == b"Hi\x00\x00\x00\x00\x00\x00"

    def test_serialize_too_long(self):
        """SerializationError when string is too long."""

        class S(Struct):
            name = FixedString(4)

        s = S(name="Hello")  # 5 bytes, field is 4
        with pytest.raises(SerializationError):
            s.to_bytes()

    def test_custom_encoding(self):
        """Custom encoding support."""

        class S(Struct):
            text = FixedString(4, encoding="ascii")

        raw = b"Hi\x00\x00"
        s = S.parse(raw)
        assert s.text == "Hi"

    def test_euc_kr_encoding(self):
        """EUC-KR encoding for Korean text."""

        class S(Struct):
            text = FixedString(6, encoding="euc-kr")

        # "한글" in EUC-KR is 4 bytes
        korean = "한글"
        encoded = korean.encode("euc-kr")
        raw = encoded + b"\x00" * (6 - len(encoded))
        s = S.parse(raw)
        assert s.text == "한글"

    def test_custom_padding(self):
        """Custom padding character."""

        class S(Struct):
            name = FixedString(8, padding=b" ")

        s = S.parse(b"Hi      ")
        assert s.name == "Hi"

        s2 = S(name="Hi")
        assert s2.to_bytes() == b"Hi      "

    def test_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            name = FixedString(10)

        original = b"TestValue\x00"
        s = S.parse(original)
        assert s.to_bytes() == original


class TestString:
    """Tests for variable-length String field."""

    def test_parse_with_fixed_length(self):
        """Parse string with fixed length."""

        class S(Struct):
            text = String(length=5)

        s = S.parse(b"Hello")
        assert s.text == "Hello"

    def test_parse_with_ref_length(self):
        """Parse string with length from Ref."""

        class S(Struct):
            length = UInt8()
            text = String(length=Ref("length"))

        raw = bytes([0x05]) + b"Hello"
        s = S.parse(raw)
        assert s.length == 5
        assert s.text == "Hello"

    def test_serialize_with_ref_length(self):
        """Serialize string with Ref length."""

        class S(Struct):
            length = UInt8()
            text = String(length=Ref("length"))

        s = S(length=5, text="Hello")
        assert s.to_bytes() == bytes([0x05]) + b"Hello"

    def test_dumb_serialization(self):
        """Serialization doesn't validate length consistency."""

        class S(Struct):
            length = UInt8()
            text = String(length=Ref("length"))

        # Length says 3, but text is 5 chars - no error
        s = S(length=3, text="Hello")
        raw = s.to_bytes()
        assert raw == bytes([0x03]) + b"Hello"

    def test_utf8_encoding(self):
        """UTF-8 encoding for multibyte characters."""

        class S(Struct):
            length = UInt8()
            text = String(length=Ref("length"), encoding="utf-8")

        # Korean text: 한글 (6 bytes in UTF-8)
        korean = "한글"
        raw = bytes([len(korean.encode("utf-8"))]) + korean.encode("utf-8")
        s = S.parse(raw)
        assert s.text == "한글"


class TestNullTerminatedString:
    """Tests for NullTerminatedString field."""

    def test_parse_null_terminated(self):
        """Parse null-terminated string."""

        class S(Struct):
            class Meta:
                trailing_data = "ignore"

            name = NullTerminatedString()

        s = S.parse(b"Hello\x00World")
        assert s.name == "Hello"

    def test_parse_at_eof(self):
        """Parse string at end of data (no null)."""

        class S(Struct):
            name = NullTerminatedString()

        s = S.parse(b"Hello")
        assert s.name == "Hello"

    def test_serialize_with_null(self):
        """Serialize with null terminator."""

        class S(Struct):
            name = NullTerminatedString()

        s = S(name="Hello")
        assert s.to_bytes() == b"Hello\x00"

    def test_serialize_without_null(self):
        """Serialize without null terminator."""

        class S(Struct):
            name = NullTerminatedString(include_null=False)

        s = S(name="Hello")
        assert s.to_bytes() == b"Hello"

    def test_empty_string(self):
        """Parse and serialize empty string."""

        class S(Struct):
            class Meta:
                trailing_data = "ignore"

            name = NullTerminatedString()

        s = S.parse(b"\x00rest")
        assert s.name == ""

        s2 = S(name="")
        assert s2.to_bytes() == b"\x00"

    def test_max_length(self):
        """Respect max_length limit."""

        class S(Struct):
            class Meta:
                trailing_data = "ignore"

            name = NullTerminatedString(max_length=5)

        s = S.parse(b"HelloWorld\x00")
        assert s.name == "Hello"  # Truncated at 5


class TestStringWithStruct:
    """Tests for string fields in complex structs."""

    def test_mixed_string_types(self):
        """Mix of fixed and variable strings."""

        class S(Struct):
            class Meta:
                trailing_data = "ignore"

            header = FixedString(4)
            name_len = UInt8()
            name = String(length=Ref("name_len"))
            trailer = NullTerminatedString()

        raw = b"HDR\x00" + bytes([0x05]) + b"Hello" + b"World\x00extra"
        s = S.parse(raw)
        assert s.header == "HDR"
        assert s.name == "Hello"
        assert s.trailer == "World"
