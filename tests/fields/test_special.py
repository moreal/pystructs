"""Tests for special field types."""

from enum import IntEnum

from pystructs import Bool, Enum, Flags, Padding, Ref, Struct, UInt8, UInt16


class TestBool:
    """Tests for Bool field."""

    def test_parse_true(self):
        """Parse non-zero as True."""

        class S(Struct):
            flag = Bool()

        s = S.parse(bytes([0x01]))
        assert s.flag is True

        s2 = S.parse(bytes([0xFF]))
        assert s2.flag is True

    def test_parse_false(self):
        """Parse zero as False."""

        class S(Struct):
            flag = Bool()

        s = S.parse(bytes([0x00]))
        assert s.flag is False

    def test_serialize_true(self):
        """Serialize True as 0x01."""

        class S(Struct):
            flag = Bool()

        s = S(flag=True)
        assert s.to_bytes() == bytes([0x01])

    def test_serialize_false(self):
        """Serialize False as 0x00."""

        class S(Struct):
            flag = Bool()

        s = S(flag=False)
        assert s.to_bytes() == bytes([0x00])

    def test_bool_default(self):
        """Default value for Bool."""

        class S(Struct):
            enabled = Bool(default=True)
            disabled = Bool(default=False)

        s = S()
        assert s.enabled is True
        assert s.disabled is False

    def test_bool_get_size(self):
        """Bool is always 1 byte."""

        class S(Struct):
            flag = Bool()

        s = S(flag=True)
        assert s.get_size() == 1

    def test_bool_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            a = Bool()
            b = Bool()
            c = Bool()

        raw = bytes([0x01, 0x00, 0xFF])
        s = S.parse(raw)
        assert s.a is True
        assert s.b is False
        assert s.c is True
        # Serialize normalizes to 0x00/0x01
        assert s.to_bytes() == bytes([0x01, 0x00, 0x01])


class TestPadding:
    """Tests for Padding field."""

    def test_parse_padding_fixed(self):
        """Parse fixed-size padding."""

        class S(Struct):
            value = UInt8()
            _pad = Padding(size=3)
            data = UInt8()

        raw = bytes([0x01, 0xAA, 0xBB, 0xCC, 0x02])
        s = S.parse(raw)
        assert s.value == 1
        assert s.data == 2
        assert s._pad is None  # Padding is not stored

    def test_serialize_padding_fixed(self):
        """Serialize fixed-size padding."""

        class S(Struct):
            value = UInt8()
            _pad = Padding(size=3)
            data = UInt8()

        s = S(value=1, data=2)
        assert s.to_bytes() == bytes([0x01, 0x00, 0x00, 0x00, 0x02])

    def test_padding_custom_fill(self):
        """Padding with custom fill byte."""

        class S(Struct):
            value = UInt8()
            _pad = Padding(size=4, fill=0xFF)

        s = S(value=0x42)
        assert s.to_bytes() == bytes([0x42, 0xFF, 0xFF, 0xFF, 0xFF])

    def test_padding_with_ref(self):
        """Padding with Ref for dynamic size."""

        class S(Struct):
            pad_size = UInt8()
            _pad = Padding(size=Ref("pad_size"))
            data = UInt8()

        raw = bytes([0x03, 0xAA, 0xBB, 0xCC, 0x42])
        s = S.parse(raw)
        assert s.pad_size == 3
        assert s.data == 0x42

    def test_padding_get_size(self):
        """get_size returns correct padding size."""

        class S(Struct):
            _pad = Padding(size=7)

        s = S()
        assert s.get_size() == 7

    def test_padding_alignment(self):
        """Use padding for alignment."""

        class AlignedData(Struct):
            small = UInt8()
            _pad = Padding(size=3)  # Align to 4 bytes
            large = UInt16()

        raw = bytes([0x01, 0x00, 0x00, 0x00, 0x34, 0x12])
        s = AlignedData.parse(raw)
        assert s.small == 1
        assert s.large == 0x1234


class TestFlags:
    """Tests for Flags field."""

    def test_parse_flags(self):
        """Parse bit flags."""

        class S(Struct):
            perms = Flags(
                size=1,
                flags={
                    "READ": 0x01,
                    "WRITE": 0x02,
                    "EXECUTE": 0x04,
                },
            )

        s = S.parse(bytes([0x05]))  # READ | EXECUTE
        assert "READ" in s.perms
        assert "EXECUTE" in s.perms
        assert "WRITE" not in s.perms

    def test_flags_value(self):
        """FlagSet.value returns raw integer."""

        class S(Struct):
            flags = Flags(
                size=1,
                flags={
                    "A": 0x01,
                    "B": 0x02,
                    "C": 0x04,
                },
            )

        s = S.parse(bytes([0x07]))
        assert s.flags.value == 7

    def test_serialize_flags_from_set(self):
        """Serialize flags from set of names."""

        class S(Struct):
            flags = Flags(
                size=1,
                flags={
                    "READ": 0x01,
                    "WRITE": 0x02,
                    "EXECUTE": 0x04,
                },
            )

        s = S(flags={"READ", "EXECUTE"})
        assert s.to_bytes() == bytes([0x05])

    def test_serialize_flags_from_int(self):
        """Serialize flags from integer."""

        class S(Struct):
            flags = Flags(
                size=1,
                flags={
                    "A": 0x01,
                    "B": 0x02,
                },
            )

        s = S(flags=0x03)
        assert s.to_bytes() == bytes([0x03])

    def test_serialize_flags_from_flagset(self):
        """Serialize flags from FlagSet."""

        class S(Struct):
            flags = Flags(
                size=1,
                flags={
                    "X": 0x10,
                    "Y": 0x20,
                },
            )

        s1 = S.parse(bytes([0x30]))
        s2 = S(flags=s1.flags)
        assert s2.to_bytes() == bytes([0x30])

    def test_flags_2_bytes(self):
        """Flags with 2-byte size."""

        class S(Struct):
            flags = Flags(
                size=2,
                flags={
                    "BIT_0": 0x0001,
                    "BIT_8": 0x0100,
                    "BIT_15": 0x8000,
                },
            )

        s = S.parse(bytes([0x01, 0x81]))  # BIT_0 | BIT_8 | BIT_15
        assert "BIT_0" in s.flags
        assert "BIT_8" in s.flags
        assert "BIT_15" in s.flags
        assert s.flags.value == 0x8101

    def test_flags_round_trip(self):
        """Round-trip parse and serialize."""

        class S(Struct):
            flags = Flags(
                size=1,
                flags={
                    "A": 0x01,
                    "B": 0x02,
                    "C": 0x04,
                    "D": 0x08,
                },
            )

        raw = bytes([0x0A])  # B | D
        s = S.parse(raw)
        assert s.to_bytes() == raw

    def test_flags_default(self):
        """Default value for Flags."""

        class S(Struct):
            flags = Flags(
                size=1,
                flags={
                    "ENABLED": 0x01,
                    "VISIBLE": 0x02,
                },
                default={"ENABLED"},
            )

        s = S()
        assert s.flags == {"ENABLED"}


class TestEnum:
    """Tests for Enum field."""

    def test_parse_enum(self):
        """Parse enum value."""

        class MessageType(IntEnum):
            REQUEST = 1
            RESPONSE = 2
            ERROR = 3

        class S(Struct):
            msg_type = Enum(MessageType, size=1)

        s = S.parse(bytes([0x02]))
        assert s.msg_type == MessageType.RESPONSE
        assert s.msg_type == 2

    def test_serialize_enum(self):
        """Serialize enum value."""

        class Status(IntEnum):
            OK = 0
            PENDING = 1
            FAILED = 2

        class S(Struct):
            status = Enum(Status, size=1)

        s = S(status=Status.FAILED)
        assert s.to_bytes() == bytes([0x02])

    def test_serialize_enum_from_int(self):
        """Serialize enum from integer."""

        class Type(IntEnum):
            A = 10
            B = 20

        class S(Struct):
            t = Enum(Type, size=1)

        s = S(t=20)
        assert s.to_bytes() == bytes([0x14])

    def test_enum_2_bytes(self):
        """Enum with 2-byte size."""

        class BigEnum(IntEnum):
            SMALL = 1
            MEDIUM = 256
            LARGE = 0x1234

        class S(Struct):
            value = Enum(BigEnum, size=2)

        s = S.parse(bytes([0x34, 0x12]))
        assert s.value == BigEnum.LARGE
        assert s.value == 0x1234

    def test_enum_unknown_value(self):
        """Unknown enum value returns raw int (dumb by default)."""

        class KnownType(IntEnum):
            A = 1
            B = 2

        class S(Struct):
            t = Enum(KnownType, size=1)

        s = S.parse(bytes([0xFF]))
        # Unknown value - returns raw int, not enum member
        assert s.t == 0xFF
        assert not isinstance(s.t, KnownType)

    def test_enum_round_trip(self):
        """Round-trip parse and serialize."""

        class Color(IntEnum):
            RED = 1
            GREEN = 2
            BLUE = 3

        class S(Struct):
            color = Enum(Color, size=1)

        raw = bytes([0x02])
        s = S.parse(raw)
        assert s.color == Color.GREEN
        assert s.to_bytes() == raw

    def test_enum_default(self):
        """Default value for Enum."""

        class Priority(IntEnum):
            LOW = 0
            NORMAL = 1
            HIGH = 2

        class S(Struct):
            priority = Enum(Priority, size=1, default=Priority.NORMAL)

        s = S()
        assert s.priority == Priority.NORMAL

    def test_enum_in_complex_struct(self):
        """Enum in a complex struct."""

        class Command(IntEnum):
            GET = 1
            SET = 2
            DELETE = 3

        class Status(IntEnum):
            SUCCESS = 0
            ERROR = 1

        class Response(Struct):
            command = Enum(Command, size=1)
            status = Enum(Status, size=1)
            data_len = UInt8()

        raw = bytes([0x02, 0x00, 0x0A])
        r = Response.parse(raw)
        assert r.command == Command.SET
        assert r.status == Status.SUCCESS
        assert r.data_len == 10


class TestMixedSpecialFields:
    """Tests combining different special field types."""

    def test_bool_and_flags(self):
        """Bool and Flags in same struct."""

        class S(Struct):
            enabled = Bool()
            perms = Flags(
                size=1,
                flags={
                    "R": 0x01,
                    "W": 0x02,
                },
            )

        raw = bytes([0x01, 0x03])
        s = S.parse(raw)
        assert s.enabled is True
        assert "R" in s.perms
        assert "W" in s.perms

    def test_enum_and_padding(self):
        """Enum and Padding in same struct."""

        class Type(IntEnum):
            A = 1
            B = 2

        class S(Struct):
            t = Enum(Type, size=1)
            _pad = Padding(size=3)
            value = UInt8()

        raw = bytes([0x01, 0x00, 0x00, 0x00, 0x42])
        s = S.parse(raw)
        assert s.t == Type.A
        assert s.value == 0x42

    def test_all_special_fields(self):
        """All special field types in one struct."""

        class Mode(IntEnum):
            READ = 1
            WRITE = 2

        class Config(Struct):
            enabled = Bool()
            mode = Enum(Mode, size=1)
            _reserved = Padding(size=2)
            flags = Flags(
                size=1,
                flags={
                    "VERBOSE": 0x01,
                    "DEBUG": 0x02,
                },
            )

        raw = bytes([0x01, 0x02, 0x00, 0x00, 0x03])
        c = Config.parse(raw)
        assert c.enabled is True
        assert c.mode == Mode.WRITE
        assert "VERBOSE" in c.flags
        assert "DEBUG" in c.flags
