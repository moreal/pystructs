"""Tests for floating-point field types."""

import math
import struct

from pystructs import Float32, Float64, Struct, UInt8


class TestFloat32:
    """Tests for Float32 field."""

    def test_parse_float32(self):
        """Parse a 32-bit float."""

        class S(Struct):
            value = Float32()

        raw = struct.pack("<f", 3.14159)
        s = S.parse(raw)
        assert abs(s.value - 3.14159) < 0.0001

    def test_parse_float32_big_endian(self):
        """Parse a 32-bit float with big endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Float32()

        raw = struct.pack(">f", 3.14159)
        s = S.parse(raw)
        assert abs(s.value - 3.14159) < 0.0001

    def test_serialize_float32(self):
        """Serialize a 32-bit float."""

        class S(Struct):
            value = Float32()

        s = S(value=2.71828)
        raw = s.to_bytes()
        assert raw == struct.pack("<f", 2.71828)

    def test_serialize_float32_big_endian(self):
        """Serialize a 32-bit float with big endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Float32()

        s = S(value=2.71828)
        raw = s.to_bytes()
        assert raw == struct.pack(">f", 2.71828)

    def test_field_level_endian(self):
        """Field-level endian overrides struct-level."""

        class S(Struct):
            class Meta:
                endian = "little"

            value = Float32(endian="big")

        raw = struct.pack(">f", 1.5)
        s = S.parse(raw)
        assert abs(s.value - 1.5) < 0.0001

    def test_float32_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            a = Float32()
            b = Float32()

        original = struct.pack("<ff", 1.23, 4.56)
        s = S.parse(original)
        assert s.to_bytes() == original

    def test_float32_special_values(self):
        """Handle special float values."""

        class S(Struct):
            value = Float32()

        # Positive infinity
        raw_inf = struct.pack("<f", float("inf"))
        s_inf = S.parse(raw_inf)
        assert math.isinf(s_inf.value) and s_inf.value > 0

        # Negative infinity
        raw_neg_inf = struct.pack("<f", float("-inf"))
        s_neg_inf = S.parse(raw_neg_inf)
        assert math.isinf(s_neg_inf.value) and s_neg_inf.value < 0

        # NaN
        raw_nan = struct.pack("<f", float("nan"))
        s_nan = S.parse(raw_nan)
        assert math.isnan(s_nan.value)

    def test_float32_default(self):
        """Default value for Float32."""

        class S(Struct):
            value = Float32(default=1.5)

        s = S()
        assert s.value == 1.5

    def test_float32_get_size(self):
        """Float32 is always 4 bytes."""

        class S(Struct):
            value = Float32()

        s = S(value=0.0)
        assert s.get_size() == 4


class TestFloat64:
    """Tests for Float64 field."""

    def test_parse_float64(self):
        """Parse a 64-bit float."""

        class S(Struct):
            value = Float64()

        raw = struct.pack("<d", 3.141592653589793)
        s = S.parse(raw)
        assert abs(s.value - 3.141592653589793) < 1e-15

    def test_parse_float64_big_endian(self):
        """Parse a 64-bit float with big endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Float64()

        raw = struct.pack(">d", 3.141592653589793)
        s = S.parse(raw)
        assert abs(s.value - 3.141592653589793) < 1e-15

    def test_serialize_float64(self):
        """Serialize a 64-bit float."""

        class S(Struct):
            value = Float64()

        s = S(value=2.718281828459045)
        raw = s.to_bytes()
        assert raw == struct.pack("<d", 2.718281828459045)

    def test_serialize_float64_big_endian(self):
        """Serialize a 64-bit float with big endian."""

        class S(Struct):
            class Meta:
                endian = "big"

            value = Float64()

        s = S(value=2.718281828459045)
        raw = s.to_bytes()
        assert raw == struct.pack(">d", 2.718281828459045)

    def test_float64_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            a = Float64()
            b = Float64()

        original = struct.pack("<dd", 1.23456789012345, 9.87654321098765)
        s = S.parse(original)
        assert s.to_bytes() == original

    def test_float64_high_precision(self):
        """Float64 maintains high precision."""

        class S(Struct):
            value = Float64()

        original_value = 1.2345678901234567890
        raw = struct.pack("<d", original_value)
        s = S.parse(raw)
        # Should maintain at least 15 digits of precision
        assert abs(s.value - original_value) < 1e-15

    def test_float64_get_size(self):
        """Float64 is always 8 bytes."""

        class S(Struct):
            value = Float64()

        s = S(value=0.0)
        assert s.get_size() == 8


class TestMixedFloats:
    """Tests for mixed float and integer fields."""

    def test_float32_with_integers(self):
        """Float32 mixed with integers."""

        class Point(Struct):
            id = UInt8()
            x = Float32()
            y = Float32()
            z = Float32()

        raw = bytes([0x01]) + struct.pack("<fff", 1.0, 2.0, 3.0)
        p = Point.parse(raw)
        assert p.id == 1
        assert abs(p.x - 1.0) < 0.0001
        assert abs(p.y - 2.0) < 0.0001
        assert abs(p.z - 3.0) < 0.0001

    def test_float64_with_integers(self):
        """Float64 mixed with integers."""

        class Measurement(Struct):
            id = UInt8()
            value = Float64()
            flags = UInt8()

        raw = bytes([0x42]) + struct.pack("<d", 123.456) + bytes([0xFF])
        m = Measurement.parse(raw)
        assert m.id == 0x42
        assert abs(m.value - 123.456) < 1e-10
        assert m.flags == 0xFF
