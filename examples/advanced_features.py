#!/usr/bin/env python3
"""Advanced features examples for pystructs.

This module demonstrates advanced features:
- Conditional fields
- Switch (tagged unions)
- Validation system
- BitStruct for bit-level parsing
- Complex nested structures
"""

from enum import IntEnum

from pystructs import (
    Array,
    Bit,
    Bits,
    BitStruct,
    Bool,
    Bytes,
    Conditional,
    Consistency,
    Custom,
    EmbeddedBitStruct,
    EmbeddedStruct,
    Enum,
    Flags,
    Len,
    OneOf,
    Padding,
    Range,
    Ref,
    Struct,
    Switch,
    SyncRule,
    UInt8,
    UInt16,
    UInt32,
    ValidationErrors,
)

# =============================================================================
# Example 1: Conditional Fields
# =============================================================================


class VersionedPacket(Struct):
    """Packet with version-dependent optional fields.

    Version 1: Basic fields only
    Version 2+: Includes extended header
    """

    version = UInt8()
    flags = UInt8()
    # Only present in version 2 and above
    extended_header = Conditional(
        UInt32(),
        when=Ref("version") >= 2,
    )
    payload_size = UInt16()


def example_conditional():
    """Demonstrate conditional fields."""
    print("=== Example 1: Conditional Fields ===")

    # Version 1 packet (no extended header)
    v1_data = bytes([0x01, 0x0F, 0x00, 0x10])  # version=1, flags=15, size=16
    v1 = VersionedPacket.parse(v1_data)
    print(f"Version 1: {v1}")
    print(f"  extended_header: {v1.extended_header} (None because version < 2)")

    # Version 2 packet (with extended header)
    v2_data = bytes(
        [
            0x02,
            0x0F,  # version=2, flags=15
            0xEF,
            0xBE,
            0xAD,
            0xDE,  # extended_header=0xDEADBEEF
            0x00,
            0x20,  # size=32
        ]
    )
    v2 = VersionedPacket.parse(v2_data)
    print(f"Version 2: {v2}")
    print(f"  extended_header: 0x{v2.extended_header:08X}")
    print()


# =============================================================================
# Example 2: Switch (Tagged Unions)
# =============================================================================


class MessageType(IntEnum):
    TEXT = 1
    BINARY = 2
    COMMAND = 3


class TextPayload(Struct):
    """Text message payload."""

    text_length = UInt8()
    text = Bytes(size=Ref("text_length"))


class BinaryPayload(Struct):
    """Binary data payload."""

    data_size = UInt16()
    data = Bytes(size=Ref("data_size"))


class CommandPayload(Struct):
    """Command payload."""

    command_id = UInt8()
    param1 = UInt32()
    param2 = UInt32()


class Message(Struct):
    """Message with type-dependent payload using Switch."""

    msg_type = UInt8()
    payload = Switch(
        discriminator=Ref("msg_type"),
        cases={
            MessageType.TEXT: TextPayload,
            MessageType.BINARY: BinaryPayload,
            MessageType.COMMAND: CommandPayload,
        },
    )


def example_switch():
    """Demonstrate Switch for tagged unions."""
    print("=== Example 2: Switch (Tagged Unions) ===")

    # Text message
    text_data = bytes([0x01, 0x05]) + b"Hello"
    text_msg = Message.parse(text_data)
    print(f"Text message: type={text_msg.msg_type}")
    print(f"  payload.text: {text_msg.payload.text.decode()}")

    # Binary message
    binary_data = bytes([0x02, 0x04, 0x00, 0xDE, 0xAD, 0xBE, 0xEF])
    binary_msg = Message.parse(binary_data)
    print(f"Binary message: type={binary_msg.msg_type}")
    print(f"  payload.data: {binary_msg.payload.data.hex()}")

    # Command message
    cmd_data = bytes(
        [
            0x03,  # type=COMMAND
            0x42,  # command_id
            0x01,
            0x00,
            0x00,
            0x00,  # param1=1
            0x02,
            0x00,
            0x00,
            0x00,  # param2=2
        ]
    )
    cmd_msg = Message.parse(cmd_data)
    print(f"Command message: type={cmd_msg.msg_type}")
    payload = cmd_msg.payload
    print(
        f"  command_id={payload.command_id}, "
        f"params=({payload.param1}, {payload.param2})"
    )
    print()


# =============================================================================
# Example 3: Validation
# =============================================================================


class ValidatedPacket(Struct):
    """Packet with comprehensive validation rules."""

    class Meta:
        validators = [
            # Ensure length matches data size
            Consistency("length", equals=Len("data")),
            # Custom validation
            Custom(
                lambda s: s.version in (1, 2, 3),
                "Version must be 1, 2, or 3",
            ),
        ]
        sync_rules = [
            SyncRule("length", from_field="data", compute=len),
        ]

    # Field with range validation
    version = UInt8(validators=[Range(min_val=1, max_val=3)])
    # Field with allowed values
    packet_type = UInt8(validators=[OneOf([0x01, 0x02, 0x03, 0xFF])])
    length = UInt8()
    data = Bytes(size=Ref("length"))


def example_validation():
    """Demonstrate validation system."""
    print("=== Example 3: Validation ===")

    # Valid packet
    valid = ValidatedPacket(
        version=2,
        packet_type=0x01,
        data=b"Hello",
    )
    valid.sync()
    print(f"Valid packet: {valid}")

    try:
        valid.validate()
        print("  Validation passed!")
    except ValidationErrors as e:
        print(f"  Validation failed: {e}")

    # Invalid version
    print("\nTrying invalid version (10)...")
    try:
        invalid = ValidatedPacket(version=10, packet_type=0x01, data=b"Test")
        invalid.sync()
        invalid.validate()
    except ValidationErrors as e:
        print(f"  Validation failed: {e}")

    # Invalid packet type
    print("\nTrying invalid packet_type (0x99)...")
    try:
        invalid = ValidatedPacket(version=1, packet_type=0x99, data=b"Test")
        invalid.sync()
        invalid.validate()
    except ValidationErrors as e:
        print(f"  Validation failed: {e}")
    print()


# =============================================================================
# Example 4: BitStruct for Bit-Level Parsing
# =============================================================================


class ControlFlags(BitStruct):
    """Control flags packed into a single byte."""

    class Meta:
        size = 1

    enabled = Bit()
    priority = Bits(3)  # 0-7
    mode = Bits(2)  # 0-3
    reserved = Bits(2)


class StatusRegister(BitStruct):
    """Hardware status register (16 bits)."""

    class Meta:
        size = 2

    error_code = Bits(4)
    warning_level = Bits(4)
    state = Bits(4)
    version = Bits(4)


class DeviceStatus(Struct):
    """Device status with bit-level fields."""

    device_id = UInt16()
    control = EmbeddedBitStruct(ControlFlags)
    status = EmbeddedBitStruct(StatusRegister)
    temperature = UInt8()


def example_bitstruct():
    """Demonstrate BitStruct for bit-level parsing."""
    print("=== Example 4: BitStruct ===")

    # Create device status
    device = DeviceStatus(
        device_id=1234,
        control=ControlFlags(enabled=True, priority=5, mode=2),
        status=StatusRegister(error_code=0, warning_level=1, state=3, version=2),
        temperature=42,
    )

    print(f"Device ID: {device.device_id}")
    print("Control flags:")
    print(f"  enabled: {device.control.enabled}")
    print(f"  priority: {device.control.priority}")
    print(f"  mode: {device.control.mode}")
    print("Status register:")
    print(f"  error_code: {device.status.error_code}")
    print(f"  warning_level: {device.status.warning_level}")
    print(f"  state: {device.status.state}")
    print(f"  version: {device.status.version}")
    print(f"Temperature: {device.temperature}")

    # Serialize and show raw bytes
    raw = device.to_bytes()
    print(f"Raw bytes ({len(raw)}): {raw.hex()}")

    # Parse back
    parsed = DeviceStatus.parse(raw)
    print(f"Parsed control.enabled: {parsed.control.enabled}")
    print()


# =============================================================================
# Example 5: Flags and Enums
# =============================================================================


class FileMode(IntEnum):
    READ = 1
    WRITE = 2
    APPEND = 3
    CREATE = 4


class FileDescriptor(Struct):
    """File descriptor with flags and enum fields."""

    mode = Enum(FileMode, size=1)
    permissions = Flags(
        size=2,
        flags={
            "OWNER_READ": 0x0100,
            "OWNER_WRITE": 0x0080,
            "OWNER_EXEC": 0x0040,
            "GROUP_READ": 0x0020,
            "GROUP_WRITE": 0x0010,
            "GROUP_EXEC": 0x0008,
            "OTHER_READ": 0x0004,
            "OTHER_WRITE": 0x0002,
            "OTHER_EXEC": 0x0001,
        },
    )
    is_directory = Bool()
    _reserved = Padding(size=1)
    size = UInt32()


def example_flags_enums():
    """Demonstrate Flags and Enum fields."""
    print("=== Example 5: Flags and Enums ===")

    fd = FileDescriptor(
        mode=FileMode.WRITE,
        permissions={"OWNER_READ", "OWNER_WRITE", "GROUP_READ"},
        is_directory=False,
        size=1024,
    )

    print("File descriptor:")
    print(f"  mode: {fd.mode.name}")
    print(f"  permissions: {fd.permissions}")
    # Calculate raw value from the set of flag names
    raw_value = (
        sum(fd.permissions.flags[name] for name in fd.permissions)
        if hasattr(fd.permissions, "flags")
        else sum(FileDescriptor.permissions.flags[name] for name in fd.permissions)
    )
    print(f"  permissions raw value: 0x{raw_value:04X}")
    print(f"  is_directory: {fd.is_directory}")
    print(f"  size: {fd.size}")

    raw = fd.to_bytes()
    print(f"Raw bytes ({len(raw)}): {raw.hex()}")

    # Check flags
    parsed = FileDescriptor.parse(raw)
    print("\nParsed permissions check:")
    print(f"  OWNER_READ in perms: {'OWNER_READ' in parsed.permissions}")
    print(f"  OTHER_WRITE in perms: {'OTHER_WRITE' in parsed.permissions}")
    print()


# =============================================================================
# Example 6: Complex Nested Structure
# =============================================================================


class AttributeType(IntEnum):
    STRING = 1
    INTEGER = 2
    BINARY = 3


class StringAttribute(Struct):
    """String attribute value."""

    length = UInt8()
    value = Bytes(size=Ref("length"))


class IntegerAttribute(Struct):
    """Integer attribute value."""

    value = UInt32()


class BinaryAttribute(Struct):
    """Binary attribute value."""

    size = UInt16()
    data = Bytes(size=Ref("size"))


class Attribute(Struct):
    """Generic attribute with typed value."""

    attr_type = UInt8()
    value = Switch(
        discriminator=Ref("attr_type"),
        cases={
            AttributeType.STRING: StringAttribute,
            AttributeType.INTEGER: IntegerAttribute,
            AttributeType.BINARY: BinaryAttribute,
        },
    )


class AttributeContainer(Struct):
    """Container holding multiple attributes."""

    class Meta:
        sync_rules = [
            SyncRule("count", from_field="attributes", compute=len),
        ]

    magic = UInt32(default=0x41545452)  # "ATTR"
    count = UInt8()
    attributes = Array(EmbeddedStruct(Attribute), count=Ref("count"))


def example_complex_nested():
    """Demonstrate complex nested structures."""
    print("=== Example 6: Complex Nested Structure ===")

    # Create attributes
    str_attr = Attribute(
        attr_type=AttributeType.STRING,
        value=StringAttribute(length=5, value=b"Hello"),
    )

    int_attr = Attribute(
        attr_type=AttributeType.INTEGER,
        value=IntegerAttribute(value=42),
    )

    bin_attr = Attribute(
        attr_type=AttributeType.BINARY,
        value=BinaryAttribute(size=4, data=bytes([0xDE, 0xAD, 0xBE, 0xEF])),
    )

    # Create container
    container = AttributeContainer(
        attributes=[str_attr, int_attr, bin_attr],
    )
    container.sync()

    print(f"Container with {container.count} attributes:")
    for i, attr in enumerate(container.attributes):
        print(f"  Attribute {i}: type={attr.attr_type}")
        if attr.attr_type == AttributeType.STRING:
            print(f"    value: {attr.value.value.decode()}")
        elif attr.attr_type == AttributeType.INTEGER:
            print(f"    value: {attr.value.value}")
        elif attr.attr_type == AttributeType.BINARY:
            print(f"    data: {attr.value.data.hex()}")

    raw = container.to_bytes()
    print(f"\nSerialized ({len(raw)} bytes): {raw.hex()}")

    # Parse back
    parsed = AttributeContainer.parse(raw)
    print(f"Parsed {parsed.count} attributes successfully")
    print()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    example_conditional()
    example_switch()
    example_validation()
    example_bitstruct()
    example_flags_enums()
    example_complex_nested()

    print("All advanced examples completed successfully!")
