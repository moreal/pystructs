"""Tests for Struct and StructMeta."""

import pytest

from pystructs import Int32, Struct, UInt8, UInt16, UInt32
from pystructs.exceptions import SerializationError, TrailingDataError, UnexpectedEOF


class TestStructMeta:
    """Tests for StructMeta metaclass."""

    def test_metaclass_collects_fields(self):
        """Metaclass collects field definitions into _fields."""

        class TestStruct(Struct):
            a = UInt8()
            b = UInt16()
            c = UInt32()

        assert "a" in TestStruct._fields
        assert "b" in TestStruct._fields
        assert "c" in TestStruct._fields
        assert len(TestStruct._fields) == 3

    def test_metaclass_preserves_field_order(self):
        """Fields are preserved in declaration order."""

        class TestStruct(Struct):
            first = UInt8()
            second = UInt16()
            third = UInt32()

        field_names = list(TestStruct._fields.keys())
        assert field_names == ["first", "second", "third"]

    def test_metaclass_inherits_fields(self):
        """Child structs inherit parent fields."""

        class Parent(Struct):
            a = UInt8()

        class Child(Parent):
            b = UInt16()

        assert "a" in Child._fields
        assert "b" in Child._fields
        assert len(Child._fields) == 2

    def test_metaclass_processes_meta_class(self):
        """Meta class options are processed."""

        class TestStruct(Struct):
            class Meta:
                endian = "big"
                trailing_data = "ignore"

            value = UInt32()

        assert TestStruct._meta.endian == "big"
        assert TestStruct._meta.trailing_data == "ignore"

    def test_metaclass_inherits_meta_options(self):
        """Child structs inherit parent Meta options."""

        class Parent(Struct):
            class Meta:
                endian = "big"

            a = UInt8()

        class Child(Parent):
            b = UInt16()

        assert Child._meta.endian == "big"


class TestStructParse:
    """Tests for Struct.parse()."""

    def test_parse_simple_struct(self):
        """Parse a simple struct from bytes."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()

        data = bytes([0x01, 0x02, 0x03])
        s = Simple.parse(data)
        assert s.a == 0x01
        assert s.b == 0x0302  # little-endian

    def test_parse_big_endian(self):
        """Parse with big-endian byte order."""

        class BigEndian(Struct):
            class Meta:
                endian = "big"

            value = UInt16()

        data = bytes([0x01, 0x02])
        s = BigEndian.parse(data)
        assert s.value == 0x0102

    def test_parse_little_endian(self):
        """Parse with little-endian byte order."""

        class LittleEndian(Struct):
            class Meta:
                endian = "little"

            value = UInt16()

        data = bytes([0x01, 0x02])
        s = LittleEndian.parse(data)
        assert s.value == 0x0201

    def test_parse_trailing_data_error(self):
        """Trailing data raises error by default."""

        class Simple(Struct):
            a = UInt8()

        data = bytes([0x01, 0x02, 0x03])
        with pytest.raises(TrailingDataError) as exc_info:
            Simple.parse(data)
        assert exc_info.value.count == 2

    def test_parse_trailing_data_allowed(self):
        """Trailing data can be allowed."""

        class Simple(Struct):
            a = UInt8()

        data = bytes([0x01, 0x02, 0x03])
        s = Simple.parse(data, allow_trailing=True)
        assert s.a == 0x01

    def test_parse_trailing_data_ignore_policy(self):
        """Trailing data can be ignored via Meta."""

        class Simple(Struct):
            class Meta:
                trailing_data = "ignore"

            a = UInt8()

        data = bytes([0x01, 0x02, 0x03])
        s = Simple.parse(data)
        assert s.a == 0x01

    def test_parse_unexpected_eof(self):
        """UnexpectedEOF raised when data is too short."""

        class Simple(Struct):
            a = UInt32()

        data = bytes([0x01, 0x02])
        with pytest.raises(UnexpectedEOF) as exc_info:
            Simple.parse(data)
        assert exc_info.value.expected == 4
        assert exc_info.value.got == 2


class TestStructToBytes:
    """Tests for Struct.to_bytes()."""

    def test_to_bytes_simple(self):
        """Serialize a simple struct to bytes."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()

        s = Simple(a=0x01, b=0x0302)
        data = s.to_bytes()
        assert data == bytes([0x01, 0x02, 0x03])

    def test_to_bytes_big_endian(self):
        """Serialize with big-endian byte order."""

        class BigEndian(Struct):
            class Meta:
                endian = "big"

            value = UInt16()

        s = BigEndian(value=0x0102)
        data = s.to_bytes()
        assert data == bytes([0x01, 0x02])

    def test_to_bytes_missing_required_field(self):
        """SerializationError raised for missing required field."""
        from pystructs.base import FixedField

        # Create a custom field without default to test missing required
        class NoDefaultField(FixedField):
            size = 2

            def parse(self, buffer, instance):
                data = buffer.read(2)
                return int.from_bytes(data, "little")

            def serialize(self, value, instance):
                return value.to_bytes(2, "little")

        class Simple(Struct):
            a = UInt8()
            b = NoDefaultField()

        s = Simple(a=0x01)  # b is missing and has no default
        with pytest.raises(SerializationError) as exc_info:
            s.to_bytes()
        assert "b" in str(exc_info.value)

    def test_to_bytes_with_defaults(self):
        """Default values are used in serialization."""

        class WithDefaults(Struct):
            a = UInt8(default=0x42)
            b = UInt16(default=0x1234)

        s = WithDefaults()
        data = s.to_bytes()
        assert data == bytes([0x42, 0x34, 0x12])  # little-endian


class TestStructInstance:
    """Tests for Struct instance behavior."""

    def test_field_access_via_attribute(self):
        """Fields can be accessed as attributes."""

        class Simple(Struct):
            value = UInt32()

        s = Simple(value=12345)
        assert s.value == 12345

    def test_field_modification_via_attribute(self):
        """Fields can be modified via attribute assignment."""

        class Simple(Struct):
            value = UInt32()

        s = Simple(value=0)
        s.value = 99999
        assert s.value == 99999

    def test_struct_equality(self):
        """Structs with same values are equal."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()

        s1 = Simple(a=1, b=2)
        s2 = Simple(a=1, b=2)
        s3 = Simple(a=1, b=3)

        assert s1 == s2
        assert s1 != s3

    def test_struct_repr(self):
        """Struct repr shows field values."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()

        s = Simple(a=1, b=2)
        r = repr(s)
        assert "Simple" in r
        assert "a=1" in r
        assert "b=2" in r

    def test_struct_to_dict(self):
        """Struct can be converted to dict."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()

        s = Simple(a=1, b=2)
        d = s.to_dict()
        assert d == {"a": 1, "b": 2}

    def test_struct_get_size(self):
        """get_size returns correct total size."""

        class Simple(Struct):
            a = UInt8()  # 1 byte
            b = UInt16()  # 2 bytes
            c = UInt32()  # 4 bytes

        s = Simple(a=0, b=0, c=0)
        assert s.get_size() == 7

    def test_get_fixed_size_class_method(self):
        """get_fixed_size returns total size for fixed structs."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()

        assert Simple.get_fixed_size() == 3

    def test_attribute_error_for_unknown_field(self):
        """AttributeError raised for unknown field access."""

        class Simple(Struct):
            a = UInt8()

        s = Simple(a=1)
        with pytest.raises(AttributeError):
            _ = s.unknown_field


class TestStructRoundTrip:
    """Tests for parse/to_bytes round-trip."""

    def test_round_trip_simple(self):
        """Data survives parse/to_bytes round-trip."""

        class Simple(Struct):
            a = UInt8()
            b = UInt16()
            c = UInt32()

        original = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
        s = Simple.parse(original)
        result = s.to_bytes()
        assert result == original

    def test_round_trip_big_endian(self):
        """Big-endian data survives round-trip."""

        class BigEndian(Struct):
            class Meta:
                endian = "big"

            a = UInt16()
            b = UInt32()

        original = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
        s = BigEndian.parse(original)
        result = s.to_bytes()
        assert result == original

    def test_round_trip_signed_integers(self):
        """Signed integers survive round-trip."""

        class Signed(Struct):
            a = Int32()

        original = bytes([0xFF, 0xFF, 0xFF, 0xFF])  # -1 in little-endian
        s = Signed.parse(original)
        assert s.a == -1
        result = s.to_bytes()
        assert result == original
