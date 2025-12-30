"""Tests for bytes field types."""

import pytest

from pystructs import Bytes, FixedBytes, Ref, Struct, UInt8, UInt16
from pystructs.exceptions import UnexpectedEOF


class TestFixedBytes:
    """Tests for FixedBytes field."""

    def test_parse_fixed_bytes(self):
        """Parse fixed-length bytes."""

        class S(Struct):
            data = FixedBytes(4)

        s = S.parse(b"\x01\x02\x03\x04")
        assert s.data == b"\x01\x02\x03\x04"

    def test_serialize_fixed_bytes(self):
        """Serialize fixed-length bytes."""

        class S(Struct):
            data = FixedBytes(4)

        s = S(data=b"\x01\x02\x03\x04")
        assert s.to_bytes() == b"\x01\x02\x03\x04"

    def test_unexpected_eof(self):
        """UnexpectedEOF when data is too short."""

        class S(Struct):
            data = FixedBytes(4)

        with pytest.raises(UnexpectedEOF):
            S.parse(b"\x01\x02")

    def test_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            data = FixedBytes(8)

        original = b"\x00\x11\x22\x33\x44\x55\x66\x77"
        s = S.parse(original)
        assert s.to_bytes() == original


class TestBytes:
    """Tests for variable-length Bytes field."""

    def test_parse_with_fixed_size(self):
        """Parse bytes with fixed size."""

        class S(Struct):
            data = Bytes(size=4)

        s = S.parse(b"\x01\x02\x03\x04")
        assert s.data == b"\x01\x02\x03\x04"

    def test_parse_with_ref_size(self):
        """Parse bytes with size from Ref."""

        class S(Struct):
            length = UInt8()
            data = Bytes(size=Ref("length"))

        raw = bytes([0x05, 0x01, 0x02, 0x03, 0x04, 0x05])
        s = S.parse(raw)
        assert s.length == 5
        assert s.data == b"\x01\x02\x03\x04\x05"

    def test_serialize_with_ref_size(self):
        """Serialize bytes with Ref size (dumb serialization)."""

        class S(Struct):
            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=3, data=b"\x01\x02\x03")
        raw = s.to_bytes()
        assert raw == bytes([0x03, 0x01, 0x02, 0x03])

    def test_dumb_serialization(self):
        """Serialization doesn't validate size consistency."""

        class S(Struct):
            length = UInt8()
            data = Bytes(size=Ref("length"))

        # Length says 3, but data is 5 bytes - no error (dumb serialization)
        s = S(length=3, data=b"\x01\x02\x03\x04\x05")
        raw = s.to_bytes()
        assert raw == bytes([0x03, 0x01, 0x02, 0x03, 0x04, 0x05])

    def test_unexpected_eof(self):
        """UnexpectedEOF when data is too short for size."""

        class S(Struct):
            length = UInt8()
            data = Bytes(size=Ref("length"))

        raw = bytes([0x10, 0x01, 0x02])  # length=16 but only 2 bytes
        with pytest.raises(UnexpectedEOF):
            S.parse(raw)

    def test_get_size(self):
        """get_size returns correct size."""

        class S(Struct):
            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=10, data=b"0123456789")
        assert s.get_size() == 11  # 1 + 10


class TestBytesWithStruct:
    """Tests for Bytes field in complex structs."""

    def test_multiple_variable_fields(self):
        """Multiple variable-length fields."""

        class S(Struct):
            len1 = UInt8()
            data1 = Bytes(size=Ref("len1"))
            len2 = UInt8()
            data2 = Bytes(size=Ref("len2"))

        raw = bytes([0x02, 0xAA, 0xBB, 0x03, 0xCC, 0xDD, 0xEE])
        s = S.parse(raw)
        assert s.data1 == b"\xaa\xbb"
        assert s.data2 == b"\xcc\xdd\xee"

    def test_round_trip_variable_bytes(self):
        """Round-trip with variable bytes."""

        class S(Struct):
            length = UInt16()
            data = Bytes(size=Ref("length"))

        original = bytes([0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        s = S.parse(original)
        assert s.to_bytes() == original
