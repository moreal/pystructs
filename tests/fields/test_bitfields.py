"""Tests for bit-level field types."""

import pytest

from pystructs import (
    Bit,
    Bits,
    BitStruct,
    EmbeddedBitStruct,
    Struct,
    UInt8,
    UInt16,
)


class TestBit:
    """Tests for Bit field."""

    def test_bit_extract(self):
        """Extract single bit."""
        bit = Bit()
        assert bit.extract(0b00000001, 0) is True
        assert bit.extract(0b00000000, 0) is False
        assert bit.extract(0b00000010, 1) is True
        assert bit.extract(0b00000010, 0) is False

    def test_bit_insert(self):
        """Insert single bit."""
        bit = Bit()
        # Set bit
        assert bit.insert(0b00000000, True, 0) == 0b00000001
        assert bit.insert(0b00000000, True, 3) == 0b00001000
        # Clear bit
        assert bit.insert(0b11111111, False, 0) == 0b11111110
        assert bit.insert(0b11111111, False, 7) == 0b01111111


class TestBits:
    """Tests for Bits field."""

    def test_bits_extract(self):
        """Extract multiple bits."""
        bits3 = Bits(3)
        assert bits3.extract(0b11111111, 0) == 0b111
        assert bits3.extract(0b01010101, 2) == 0b101

        bits5 = Bits(5)
        assert bits5.extract(0b11111111, 0) == 0b11111
        assert bits5.extract(0b11111111, 3) == 0b11111

    def test_bits_insert(self):
        """Insert multiple bits."""
        bits3 = Bits(3)
        # Set bits
        assert bits3.insert(0b00000000, 0b111, 0) == 0b00000111
        assert bits3.insert(0b00000000, 0b101, 2) == 0b00010100
        # Clear and set
        assert bits3.insert(0b11111111, 0b000, 0) == 0b11111000
        assert bits3.insert(0b11111111, 0b010, 2) == 0b11101011

    def test_bits_masking(self):
        """Value is masked to bit width."""
        bits3 = Bits(3)
        # Value 0xFF should be masked to 0b111 (7)
        assert bits3.insert(0, 0xFF, 0) == 0b00000111


class TestBitStruct:
    """Tests for BitStruct."""

    def test_parse_simple(self):
        """Parse simple BitStruct."""

        class Status(BitStruct):
            class Meta:
                size = 1

            enabled = Bit()
            ready = Bit()
            error = Bit()
            reserved = Bits(5)

        s = Status.parse(bytes([0b00000101]))  # enabled=1, ready=0, error=1
        assert s.enabled is True
        assert s.ready is False
        assert s.error is True
        assert s.reserved == 0

    def test_parse_multi_bit_fields(self):
        """Parse BitStruct with multi-bit fields."""

        class PackedByte(BitStruct):
            class Meta:
                size = 1

            type_id = Bits(3)  # 0-7
            value = Bits(5)  # 0-31

        s = PackedByte.parse(bytes([0b10110101]))
        # LSB first: type_id is bits 0-2, value is bits 3-7
        assert s.type_id == 0b101  # 5
        assert s.value == 0b10110  # 22

    def test_serialize_simple(self):
        """Serialize simple BitStruct."""

        class Flags(BitStruct):
            class Meta:
                size = 1

            a = Bit()
            b = Bit()
            c = Bit()
            d = Bit()
            e = Bit()
            f = Bit()
            g = Bit()
            h = Bit()

        f = Flags(a=True, b=False, c=True, d=False, e=True, f=False, g=True, h=False)
        assert f.to_bytes() == bytes([0b01010101])

    def test_serialize_multi_bit(self):
        """Serialize BitStruct with multi-bit fields."""

        class PackedByte(BitStruct):
            class Meta:
                size = 1

            lower = Bits(4)
            upper = Bits(4)

        p = PackedByte(lower=0x0A, upper=0x0B)
        assert p.to_bytes() == bytes([0xBA])  # 0x0B << 4 | 0x0A

    def test_round_trip(self):
        """Round-trip parse and serialize."""

        class Status(BitStruct):
            class Meta:
                size = 1

            enabled = Bit()
            mode = Bits(3)
            priority = Bits(4)

        raw = bytes([0b11010111])
        s = Status.parse(raw)
        assert s.to_bytes() == raw

    def test_two_byte_bitstruct(self):
        """BitStruct spanning 2 bytes."""

        class ExtendedStatus(BitStruct):
            class Meta:
                size = 2

            flags = Bits(4)
            version = Bits(4)
            error_code = Bits(8)

        raw = bytes([0x12, 0x34])  # 0x1234 in little-endian
        s = ExtendedStatus.parse(raw)
        # Little-endian: value = 0x3412
        # flags = bits 0-3 = 0x2
        # version = bits 4-7 = 0x1
        # error_code = bits 8-15 = 0x34
        assert s.flags == 0x2
        assert s.version == 0x1
        assert s.error_code == 0x34

        assert s.to_bytes() == raw

    def test_default_values(self):
        """Default values in BitStruct."""

        class Config(BitStruct):
            class Meta:
                size = 1

            enabled = Bit()  # Default False
            mode = Bits(3, default=5)
            level = Bits(4, default=0)

        c = Config()
        assert c.enabled is False
        assert c.mode == 5
        assert c.level == 0

    def test_attribute_access(self):
        """Get and set fields via attributes."""

        class Data(BitStruct):
            class Meta:
                size = 1

            flag = Bit()
            value = Bits(7)

        d = Data()
        d.flag = True
        d.value = 100
        assert d.flag is True
        assert d.value == 100

    def test_repr(self):
        """String representation."""

        class S(BitStruct):
            class Meta:
                size = 1

            a = Bit()
            b = Bits(7)

        s = S(a=True, b=42)
        assert "a=True" in repr(s)
        assert "b=42" in repr(s)

    def test_equality(self):
        """BitStruct equality."""

        class S(BitStruct):
            class Meta:
                size = 1

            x = Bits(8)

        s1 = S(x=10)
        s2 = S(x=10)
        s3 = S(x=20)

        assert s1 == s2
        assert s1 != s3

    def test_to_dict(self):
        """Convert to dictionary."""

        class S(BitStruct):
            class Meta:
                size = 1

            a = Bit()
            b = Bits(7)

        s = S(a=True, b=50)
        d = s.to_dict()
        assert d == {"a": True, "b": 50}

    def test_size_validation(self):
        """Meta.size must match total bits."""
        with pytest.raises(ValueError, match="expects 8 bits"):

            class BadBitStruct(BitStruct):
                class Meta:
                    size = 1  # 8 bits expected

                a = Bit()
                b = Bits(4)
                # Only 5 bits defined!


class TestBitStructMSB:
    """Tests for MSB-first bit order."""

    def test_msb_order(self):
        """MSB-first bit ordering."""

        class MsbFirst(BitStruct):
            class Meta:
                size = 1
                bit_order = "msb"

            high = Bits(4)  # Bits 7-4
            low = Bits(4)  # Bits 3-0

        raw = bytes([0xAB])
        s = MsbFirst.parse(raw)
        assert s.high == 0xA
        assert s.low == 0xB

    def test_msb_serialize(self):
        """MSB-first serialization."""

        class MsbFirst(BitStruct):
            class Meta:
                size = 1
                bit_order = "msb"

            high = Bits(4)
            low = Bits(4)

        s = MsbFirst(high=0xC, low=0xD)
        assert s.to_bytes() == bytes([0xCD])


class TestEmbeddedBitStruct:
    """Tests for EmbeddedBitStruct field in regular Struct."""

    def test_embedded_in_struct(self):
        """BitStruct embedded in regular Struct."""

        class StatusByte(BitStruct):
            class Meta:
                size = 1

            enabled = Bit()
            mode = Bits(3)
            level = Bits(4)

        class Packet(Struct):
            header = UInt8()
            status = EmbeddedBitStruct(StatusByte)
            data = UInt16()

        raw = bytes([0xAA, 0b01011101, 0x12, 0x34])
        p = Packet.parse(raw)

        assert p.header == 0xAA
        assert p.status.enabled is True
        assert p.status.mode == 0b110  # bits 1-3
        assert p.status.level == 0b0101  # bits 4-7
        assert p.data == 0x3412

    def test_serialize_embedded(self):
        """Serialize Struct with embedded BitStruct."""

        class Flags(BitStruct):
            class Meta:
                size = 1

            a = Bit()
            b = Bit()
            c = Bits(6)

        class Message(Struct):
            id = UInt8()
            flags = EmbeddedBitStruct(Flags)

        m = Message(id=42, flags=Flags(a=True, b=False, c=0x3F))
        raw = m.to_bytes()
        assert raw == bytes([42, 0b11111101])

    def test_round_trip_embedded(self):
        """Round-trip with embedded BitStruct."""

        class ControlBits(BitStruct):
            class Meta:
                size = 2

            command = Bits(4)
            flags = Bits(8)
            reserved = Bits(4)

        class Request(Struct):
            version = UInt8()
            control = EmbeddedBitStruct(ControlBits)
            payload = UInt8()

        raw = bytes([0x01, 0x12, 0x34, 0xFF])
        r = Request.parse(raw)
        assert r.to_bytes() == raw


class TestBitStructEdgeCases:
    """Edge case tests for BitStruct."""

    def test_single_bit_bitstruct(self):
        """BitStruct with 8 single-bit fields."""

        class AllBits(BitStruct):
            class Meta:
                size = 1

            b0 = Bit()
            b1 = Bit()
            b2 = Bit()
            b3 = Bit()
            b4 = Bit()
            b5 = Bit()
            b6 = Bit()
            b7 = Bit()

        raw = bytes([0b10101010])
        s = AllBits.parse(raw)
        assert s.b0 is False
        assert s.b1 is True
        assert s.b2 is False
        assert s.b3 is True
        assert s.b4 is False
        assert s.b5 is True
        assert s.b6 is False
        assert s.b7 is True

    def test_full_byte_bits(self):
        """BitStruct with single 8-bit field."""

        class ByteValue(BitStruct):
            class Meta:
                size = 1

            value = Bits(8)

        raw = bytes([0xAB])
        s = ByteValue.parse(raw)
        assert s.value == 0xAB

        s2 = ByteValue(value=0xCD)
        assert s2.to_bytes() == bytes([0xCD])

    def test_four_byte_bitstruct(self):
        """BitStruct spanning 4 bytes."""

        class LargeStruct(BitStruct):
            class Meta:
                size = 4

            field_a = Bits(10)
            field_b = Bits(10)
            field_c = Bits(12)

        raw = bytes([0x01, 0x02, 0x03, 0x04])
        s = LargeStruct.parse(raw)
        # Verify round-trip
        assert s.to_bytes() == raw
