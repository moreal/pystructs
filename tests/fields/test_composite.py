"""Tests for composite field types."""

import pytest

from pystructs import (
    Array,
    Bytes,
    Conditional,
    EmbeddedStruct,
    Ref,
    Struct,
    Switch,
    UInt8,
    UInt16,
    UInt32,
)


class TestArray:
    """Tests for Array field."""

    def test_parse_fixed_count_array(self):
        """Parse array with fixed count."""

        class S(Struct):
            values = Array(UInt8(), count=4)

        s = S.parse(bytes([0x01, 0x02, 0x03, 0x04]))
        assert s.values == [1, 2, 3, 4]

    def test_parse_ref_count_array(self):
        """Parse array with count from Ref."""

        class S(Struct):
            count = UInt8()
            values = Array(UInt16(), count=Ref("count"))

        raw = bytes([0x03, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00])
        s = S.parse(raw)
        assert s.count == 3
        assert s.values == [1, 2, 3]

    def test_serialize_fixed_count_array(self):
        """Serialize array with fixed count."""

        class S(Struct):
            values = Array(UInt8(), count=4)

        s = S(values=[1, 2, 3, 4])
        assert s.to_bytes() == bytes([0x01, 0x02, 0x03, 0x04])

    def test_serialize_ref_count_array(self):
        """Serialize array with Ref count."""

        class S(Struct):
            count = UInt8()
            values = Array(UInt16(), count=Ref("count"))

        s = S(count=3, values=[1, 2, 3])
        raw = s.to_bytes()
        assert raw == bytes([0x03, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00])

    def test_dumb_serialization(self):
        """Serialization doesn't validate count consistency."""

        class S(Struct):
            count = UInt8()
            values = Array(UInt8(), count=Ref("count"))

        # Count says 2, but values has 4 items - no error
        s = S(count=2, values=[1, 2, 3, 4])
        raw = s.to_bytes()
        assert raw == bytes([0x02, 0x01, 0x02, 0x03, 0x04])

    def test_empty_array(self):
        """Parse and serialize empty array."""

        class S(Struct):
            count = UInt8()
            values = Array(UInt8(), count=Ref("count"))

        raw = bytes([0x00])
        s = S.parse(raw)
        assert s.count == 0
        assert s.values == []

        s2 = S(count=0, values=[])
        assert s2.to_bytes() == bytes([0x00])

    def test_get_size(self):
        """get_size returns correct total size."""

        class S(Struct):
            count = UInt8()
            values = Array(UInt32(), count=Ref("count"))

        s = S(count=5, values=[0] * 5)
        # 1 byte (count) + 5 * 4 bytes (values) = 21 bytes
        assert s.get_size() == 21

    def test_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            count = UInt16()
            values = Array(UInt32(), count=Ref("count"))

        original = bytes(
            [
                0x03,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x02,
                0x00,
                0x00,
                0x00,
                0x03,
                0x00,
                0x00,
                0x00,
            ]
        )
        s = S.parse(original)
        assert s.count == 3
        assert s.values == [1, 2, 3]
        assert s.to_bytes() == original

    def test_big_endian_array(self):
        """Array with big-endian elements."""

        class S(Struct):
            class Meta:
                endian = "big"

            count = UInt8()
            values = Array(UInt16(), count=Ref("count"))

        raw = bytes([0x02, 0x00, 0x01, 0x00, 0x02])
        s = S.parse(raw)
        assert s.values == [1, 2]

    def test_nested_arrays(self):
        """Array items can be complex (though parsing nested arrays is tricky)."""

        class S(Struct):
            outer_count = UInt8()
            # Array of UInt16 pairs (simulating nested structure)
            pairs = Array(UInt16(), count=Ref("outer_count"))

        raw = bytes([0x04, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x04, 0x00])
        s = S.parse(raw)
        assert s.pairs == [1, 2, 3, 4]


class TestArrayWithMixedFields:
    """Tests for Array field with other field types."""

    def test_array_with_header(self):
        """Array preceded by header fields."""

        class S(Struct):
            magic = UInt32(default=0xDEADBEEF)
            version = UInt8()
            count = UInt8()
            items = Array(UInt16(), count=Ref("count"))

        raw = bytes(
            [0xEF, 0xBE, 0xAD, 0xDE, 0x01, 0x03, 0x0A, 0x00, 0x14, 0x00, 0x1E, 0x00]
        )
        s = S.parse(raw)
        assert s.magic == 0xDEADBEEF
        assert s.version == 1
        assert s.count == 3
        assert s.items == [10, 20, 30]

    def test_array_with_trailer(self):
        """Array followed by trailer fields."""

        class S(Struct):
            count = UInt8()
            items = Array(UInt8(), count=Ref("count"))
            checksum = UInt32()

        raw = bytes([0x03, 0x01, 0x02, 0x03, 0xEF, 0xBE, 0xAD, 0xDE])
        s = S.parse(raw)
        assert s.items == [1, 2, 3]
        assert s.checksum == 0xDEADBEEF

    def test_multiple_arrays(self):
        """Multiple arrays in one struct."""

        class S(Struct):
            count1 = UInt8()
            array1 = Array(UInt8(), count=Ref("count1"))
            count2 = UInt8()
            array2 = Array(UInt16(), count=Ref("count2"))

        raw = bytes([0x02, 0x0A, 0x0B, 0x03, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00])
        s = S.parse(raw)
        assert s.array1 == [10, 11]
        assert s.array2 == [1, 2, 3]


class TestArrayDefaults:
    """Tests for Array default values."""

    def test_default_empty_list(self):
        """Default value can be an empty list."""

        class S(Struct):
            values = Array(UInt8(), count=3, default=[])

        s = S()
        assert s.values == []

    def test_default_with_values(self):
        """Default value can be a list with values."""

        class S(Struct):
            values = Array(UInt8(), count=3, default=[1, 2, 3])

        s = S()
        assert s.values == [1, 2, 3]
        assert s.to_bytes() == bytes([0x01, 0x02, 0x03])


# === EmbeddedStruct Tests ===


class TestEmbeddedStruct:
    """Tests for EmbeddedStruct field."""

    def test_parse_embedded_struct(self):
        """Parse embedded struct from bytes."""

        class Header(Struct):
            magic = UInt32()
            version = UInt8()

        class Packet(Struct):
            header = EmbeddedStruct(Header)
            payload_size = UInt8()

        raw = bytes([0xEF, 0xBE, 0xAD, 0xDE, 0x01, 0x10])
        p = Packet.parse(raw)

        assert p.header.magic == 0xDEADBEEF
        assert p.header.version == 1
        assert p.payload_size == 16

    def test_serialize_embedded_struct(self):
        """Serialize embedded struct to bytes."""

        class Header(Struct):
            magic = UInt32()
            version = UInt8()

        class Packet(Struct):
            header = EmbeddedStruct(Header)
            data = UInt16()

        h = Header(magic=0xCAFEBABE, version=2)
        p = Packet(header=h, data=0x1234)

        raw = p.to_bytes()
        assert raw == bytes([0xBE, 0xBA, 0xFE, 0xCA, 0x02, 0x34, 0x12])

    def test_embedded_struct_parent_reference(self):
        """Embedded struct has reference to parent."""

        class Inner(Struct):
            value = UInt8()

        class Outer(Struct):
            count = UInt8()
            inner = EmbeddedStruct(Inner)

        raw = bytes([0x05, 0x0A])
        outer = Outer.parse(raw)

        # Inner should have parent reference
        assert outer.inner._parent is outer
        assert outer.inner._root is outer

    def test_embedded_struct_ref_to_parent(self):
        """Embedded struct can use Ref to access parent fields."""

        class Inner(Struct):
            data = Bytes(size=Ref("../size"))

        class Outer(Struct):
            size = UInt8()
            inner = EmbeddedStruct(Inner)

        raw = bytes([0x03, 0x41, 0x42, 0x43])  # size=3, data="ABC"
        outer = Outer.parse(raw)

        assert outer.size == 3
        assert outer.inner.data == b"ABC"

    def test_round_trip_embedded(self):
        """Round-trip parse and serialize embedded struct."""

        class Header(Struct):
            magic = UInt16()
            version = UInt8()

        class Message(Struct):
            header = EmbeddedStruct(Header)
            payload = UInt32()

        raw = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
        m = Message.parse(raw)
        assert m.to_bytes() == raw

    def test_nested_embedded_structs(self):
        """Deeply nested embedded structs."""

        class Level3(Struct):
            value = UInt8()

        class Level2(Struct):
            inner = EmbeddedStruct(Level3)
            extra = UInt8()

        class Level1(Struct):
            header = UInt16()
            nested = EmbeddedStruct(Level2)

        raw = bytes([0x01, 0x02, 0x03, 0x04])
        l1 = Level1.parse(raw)

        assert l1.header == 0x0201
        assert l1.nested.inner.value == 3
        assert l1.nested.extra == 4

    def test_get_size_embedded(self):
        """get_size returns correct size for embedded struct."""

        class Inner(Struct):
            a = UInt16()
            b = UInt32()

        class Outer(Struct):
            inner = EmbeddedStruct(Inner)

        outer = Outer(inner=Inner(a=1, b=2))
        # Inner is 2 + 4 = 6 bytes
        assert outer.get_size() == 6


# === Conditional Tests ===


class TestConditional:
    """Tests for Conditional field."""

    def test_conditional_present_with_ref(self):
        """Conditional field present when RefComparison is true."""

        class S(Struct):
            version = UInt8()
            extra = Conditional(UInt16(), when=Ref("version") >= 2)

        # Version 2 - extra is present
        raw = bytes([0x02, 0x34, 0x12])
        s = S.parse(raw)
        assert s.version == 2
        assert s.extra == 0x1234

    def test_conditional_absent_with_ref(self):
        """Conditional field absent when RefComparison is false."""

        class S(Struct):
            class Meta:
                trailing_data = "ignore"

            version = UInt8()
            extra = Conditional(UInt16(), when=Ref("version") >= 2)

        # Version 1 - extra is not present
        raw = bytes([0x01])
        s = S.parse(raw)
        assert s.version == 1
        assert s.extra is None

    def test_conditional_with_callable(self):
        """Conditional field with callable condition."""

        class S(Struct):
            flags = UInt8()
            optional = Conditional(UInt32(), when=lambda s: s.flags & 0x01)

        # Flags bit 0 set
        raw1 = bytes([0x01, 0xEF, 0xBE, 0xAD, 0xDE])
        s1 = S.parse(raw1)
        assert s1.optional == 0xDEADBEEF

        # Flags bit 0 not set
        raw2 = bytes([0x00])
        s2 = S.parse(raw2)
        assert s2.optional is None

    def test_conditional_serialize_present(self):
        """Serialize conditional field when present."""

        class S(Struct):
            version = UInt8()
            extra = Conditional(UInt16(), when=Ref("version") >= 2)

        s = S(version=2, extra=0x1234)
        raw = s.to_bytes()
        assert raw == bytes([0x02, 0x34, 0x12])

    def test_conditional_serialize_absent(self):
        """Serialize conditional field when absent."""

        class S(Struct):
            version = UInt8()
            extra = Conditional(UInt16(), when=Ref("version") >= 2)

        s = S(version=1, extra=None)
        raw = s.to_bytes()
        assert raw == bytes([0x01])

    def test_conditional_get_size_present(self):
        """get_size includes conditional field when present."""

        class S(Struct):
            version = UInt8()
            extra = Conditional(UInt32(), when=Ref("version") >= 2)

        s = S(version=2, extra=0)
        assert s.get_size() == 5  # 1 + 4

    def test_conditional_get_size_absent(self):
        """get_size excludes conditional field when absent."""

        class S(Struct):
            version = UInt8()
            extra = Conditional(UInt32(), when=Ref("version") >= 2)

        s = S(version=1, extra=None)
        assert s.get_size() == 1  # Only version

    def test_conditional_with_logical_operators(self):
        """Conditional with combined logical operators."""

        class S(Struct):
            class Meta:
                trailing_data = "ignore"

            version = UInt8()
            flags = UInt8()
            # Only if version >= 2 AND flags bit 0 set
            extra = Conditional(
                UInt16(), when=(Ref("version") >= 2) & (Ref("flags") != 0)
            )

        # Both conditions met
        raw1 = bytes([0x02, 0x01, 0x34, 0x12])
        s1 = S.parse(raw1)
        assert s1.extra == 0x1234

        # Version ok, flags not
        raw2 = bytes([0x02, 0x00])
        s2 = S.parse(raw2)
        assert s2.extra is None

        # Flags ok, version not
        raw3 = bytes([0x01, 0x01])
        s3 = S.parse(raw3)
        assert s3.extra is None

    def test_conditional_round_trip(self):
        """Round-trip with conditional field."""

        class S(Struct):
            has_extra = UInt8()
            extra = Conditional(UInt16(), when=Ref("has_extra") != 0)

        # With extra
        raw1 = bytes([0x01, 0xAB, 0xCD])
        s1 = S.parse(raw1)
        assert s1.to_bytes() == raw1

        # Without extra
        raw2 = bytes([0x00])
        s2 = S.parse(raw2)
        assert s2.to_bytes() == raw2

    def test_conditional_with_embedded_struct(self):
        """Conditional field containing embedded struct."""

        class Extra(Struct):
            a = UInt8()
            b = UInt8()

        class S(Struct):
            version = UInt8()
            extra = Conditional(EmbeddedStruct(Extra), when=Ref("version") >= 2)

        raw = bytes([0x02, 0x0A, 0x0B])
        s = S.parse(raw)
        assert s.extra.a == 10
        assert s.extra.b == 11


# === Switch Tests ===


class TestSwitch:
    """Tests for Switch field."""

    def test_switch_basic(self):
        """Basic switch between field types."""

        class S(Struct):
            msg_type = UInt8()
            payload = Switch(
                discriminator=Ref("msg_type"),
                cases={
                    1: UInt8(),
                    2: UInt16(),
                    3: UInt32(),
                },
            )

        # Type 1 - UInt8 payload
        raw1 = bytes([0x01, 0xFF])
        s1 = S.parse(raw1)
        assert s1.payload == 255

        # Type 2 - UInt16 payload
        raw2 = bytes([0x02, 0x34, 0x12])
        s2 = S.parse(raw2)
        assert s2.payload == 0x1234

        # Type 3 - UInt32 payload
        raw3 = bytes([0x03, 0xEF, 0xBE, 0xAD, 0xDE])
        s3 = S.parse(raw3)
        assert s3.payload == 0xDEADBEEF

    def test_switch_with_struct_classes(self):
        """Switch can use Struct classes (auto-wrapped in EmbeddedStruct)."""

        class TextPayload(Struct):
            length = UInt8()
            data = Bytes(size=Ref("length"))

        class BinaryPayload(Struct):
            size = UInt16()
            data = Bytes(size=Ref("size"))

        class Message(Struct):
            msg_type = UInt8()
            payload = Switch(
                discriminator=Ref("msg_type"),
                cases={
                    1: TextPayload,
                    2: BinaryPayload,
                },
            )

        # Text payload
        raw1 = bytes([0x01, 0x03, 0x41, 0x42, 0x43])  # type=1, length=3, data="ABC"
        m1 = Message.parse(raw1)
        assert m1.payload.length == 3
        assert m1.payload.data == b"ABC"

        # Binary payload
        raw2 = bytes([0x02, 0x04, 0x00, 0x01, 0x02, 0x03, 0x04])  # type=2, size=4, data
        m2 = Message.parse(raw2)
        assert m2.payload.size == 4
        assert m2.payload.data == bytes([1, 2, 3, 4])

    def test_switch_with_default(self):
        """Switch with default case."""

        class S(Struct):
            msg_type = UInt8()
            payload = Switch(
                discriminator=Ref("msg_type"),
                cases={
                    1: UInt8(),
                    2: UInt16(),
                },
                default=UInt32(),  # Fallback for unknown types
            )

        # Unknown type - uses default
        raw = bytes([0xFF, 0x01, 0x02, 0x03, 0x04])
        s = S.parse(raw)
        assert s.payload == 0x04030201

    def test_switch_no_match_raises(self):
        """Switch with no match and no default raises error."""

        class S(Struct):
            msg_type = UInt8()
            payload = Switch(
                discriminator=Ref("msg_type"),
                cases={
                    1: UInt8(),
                    2: UInt16(),
                },
            )

        raw = bytes([0xFF, 0x00, 0x00, 0x00, 0x00])
        with pytest.raises(ValueError, match="No case for discriminator"):
            S.parse(raw)

    def test_switch_serialize(self):
        """Serialize switch field."""

        class S(Struct):
            msg_type = UInt8()
            payload = Switch(
                discriminator=Ref("msg_type"),
                cases={
                    1: UInt8(),
                    2: UInt16(),
                },
            )

        # Serialize type 1
        s1 = S(msg_type=1, payload=255)
        assert s1.to_bytes() == bytes([0x01, 0xFF])

        # Serialize type 2
        s2 = S(msg_type=2, payload=0x1234)
        assert s2.to_bytes() == bytes([0x02, 0x34, 0x12])

    def test_switch_with_callable_discriminator(self):
        """Switch with callable discriminator."""

        class S(Struct):
            flags = UInt8()
            payload = Switch(
                discriminator=lambda s: s.flags & 0x03,  # Lower 2 bits
                cases={
                    0: UInt8(),
                    1: UInt16(),
                    2: UInt32(),
                },
            )

        # Flags = 0x05 -> discriminator = 1 (lower 2 bits)
        raw = bytes([0x05, 0xAB, 0xCD])
        s = S.parse(raw)
        assert s.payload == 0xCDAB

    def test_switch_get_size(self):
        """get_size returns correct size for selected case."""

        class S(Struct):
            msg_type = UInt8()
            payload = Switch(
                discriminator=Ref("msg_type"),
                cases={
                    1: UInt8(),
                    2: UInt32(),
                },
            )

        s1 = S(msg_type=1, payload=0)
        assert s1.get_size() == 2  # 1 + 1

        s2 = S(msg_type=2, payload=0)
        assert s2.get_size() == 5  # 1 + 4

    def test_switch_round_trip(self):
        """Round-trip parse and serialize."""

        class Small(Struct):
            a = UInt8()

        class Large(Struct):
            a = UInt16()
            b = UInt16()

        class S(Struct):
            kind = UInt8()
            data = Switch(
                discriminator=Ref("kind"),
                cases={
                    1: Small,
                    2: Large,
                },
            )

        # Small case
        raw1 = bytes([0x01, 0xFF])
        s1 = S.parse(raw1)
        assert s1.to_bytes() == raw1

        # Large case
        raw2 = bytes([0x02, 0x01, 0x02, 0x03, 0x04])
        s2 = S.parse(raw2)
        assert s2.to_bytes() == raw2


class TestMixedCompositeFields:
    """Tests combining different composite field types."""

    def test_array_of_embedded_structs(self):
        """Array containing embedded structs."""

        class Item(Struct):
            id = UInt8()
            value = UInt16()

        class Container(Struct):
            count = UInt8()
            items = Array(EmbeddedStruct(Item), count=Ref("count"))

        raw = bytes([0x02, 0x01, 0x0A, 0x00, 0x02, 0x14, 0x00])
        c = Container.parse(raw)

        assert c.count == 2
        assert len(c.items) == 2
        assert c.items[0].id == 1
        assert c.items[0].value == 10
        assert c.items[1].id == 2
        assert c.items[1].value == 20

    def test_embedded_struct_with_conditional(self):
        """Embedded struct containing conditional field."""

        class Inner(Struct):
            flags = UInt8()
            optional = Conditional(UInt16(), when=Ref("flags") != 0)

        class Outer(Struct):
            header = UInt8()
            inner = EmbeddedStruct(Inner)

        # With optional
        raw1 = bytes([0xAA, 0x01, 0x34, 0x12])
        o1 = Outer.parse(raw1)
        assert o1.inner.optional == 0x1234

        # Without optional
        raw2 = bytes([0xBB, 0x00])
        o2 = Outer.parse(raw2)
        assert o2.inner.optional is None

    def test_switch_with_array_cases(self):
        """Switch where cases contain arrays."""

        class S(Struct):
            kind = UInt8()
            data = Switch(
                discriminator=Ref("kind"),
                cases={
                    1: Array(UInt8(), count=2),
                    2: Array(UInt16(), count=2),
                },
            )

        # Kind 1 - array of 2 UInt8
        raw1 = bytes([0x01, 0x0A, 0x0B])
        s1 = S.parse(raw1)
        assert s1.data == [10, 11]

        # Kind 2 - array of 2 UInt16
        raw2 = bytes([0x02, 0x01, 0x00, 0x02, 0x00])
        s2 = S.parse(raw2)
        assert s2.data == [1, 2]

    def test_complex_nested_structure(self):
        """Complex structure with multiple composite types."""

        class Metadata(Struct):
            version = UInt8()
            flags = UInt8()

        class SmallPayload(Struct):
            data = UInt8()

        class LargePayload(Struct):
            count = UInt8()
            items = Array(UInt16(), count=Ref("count"))

        class Packet(Struct):
            meta = EmbeddedStruct(Metadata)
            payload = Switch(
                discriminator=Ref("meta.flags"),
                cases={
                    0: SmallPayload,
                    1: LargePayload,
                },
            )

        # Small payload
        raw1 = bytes([0x01, 0x00, 0xFF])  # version=1, flags=0, data=255
        p1 = Packet.parse(raw1)
        assert p1.meta.version == 1
        assert p1.payload.data == 255

        # Large payload
        raw2 = bytes(
            [0x02, 0x01, 0x03, 0x0A, 0x00, 0x14, 0x00, 0x1E, 0x00]
        )  # version=2, flags=1, count=3, items=[10,20,30]
        p2 = Packet.parse(raw2)
        assert p2.meta.version == 2
        assert p2.payload.count == 3
        assert p2.payload.items == [10, 20, 30]
