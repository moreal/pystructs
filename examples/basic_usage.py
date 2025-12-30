#!/usr/bin/env python3
"""Basic usage examples for pystructs.

This module demonstrates the fundamental features of pystructs:
- Defining simple structs with various field types
- Parsing binary data
- Serializing to bytes
- Using Ref for variable-length fields
- Using Meta class for configuration
"""

from pystructs import (
    Array,
    Bytes,
    FixedString,
    Int16,
    Ref,
    Struct,
    SyncRule,
    UInt8,
    UInt16,
    UInt32,
)

# =============================================================================
# Example 1: Simple Fixed-Size Struct
# =============================================================================


class SimpleHeader(Struct):
    """A simple fixed-size header structure.

    Total size: 8 bytes
    """

    magic = UInt32(default=0xDEADBEEF)
    version = UInt8(default=1)
    flags = UInt8(default=0)
    length = UInt16(default=0)


def example_simple_struct():
    """Demonstrate basic struct creation and serialization."""
    print("=== Example 1: Simple Fixed-Size Struct ===")

    # Create from keyword arguments
    header = SimpleHeader(version=2, flags=0x0F, length=100)
    print(f"Created header: {header}")
    print(f"  magic: 0x{header.magic:08X}")
    print(f"  version: {header.version}")
    print(f"  flags: 0x{header.flags:02X}")
    print(f"  length: {header.length}")

    # Serialize to bytes
    raw = header.to_bytes()
    print(f"  Serialized: {raw.hex()}")

    # Parse from bytes
    parsed = SimpleHeader.parse(raw)
    print(f"  Parsed: {parsed}")
    print()


# =============================================================================
# Example 2: Variable-Length Data with Ref
# =============================================================================


class Packet(Struct):
    """A packet with variable-length payload.

    The payload size is determined by the length field.
    """

    class Meta:
        sync_rules = [
            SyncRule("length", from_field="payload", compute=len),
        ]

    packet_type = UInt8(default=1)
    length = UInt8()
    payload = Bytes(size=Ref("length"))


def example_variable_length():
    """Demonstrate variable-length fields with Ref."""
    print("=== Example 2: Variable-Length Data with Ref ===")

    # Create packet with payload
    packet = Packet(packet_type=2, payload=b"Hello, World!")
    packet.sync()  # Auto-calculate length
    print(f"Created packet: {packet}")
    print(f"  packet_type: {packet.packet_type}")
    print(f"  length: {packet.length}")
    print(f"  payload: {packet.payload}")

    # Serialize
    raw = packet.to_bytes()
    print(f"  Serialized: {raw.hex()}")

    # Parse
    parsed = Packet.parse(raw)
    print(f"  Parsed payload: {parsed.payload.decode()}")
    print()


# =============================================================================
# Example 3: Arrays
# =============================================================================


class ScoreBoard(Struct):
    """A structure containing an array of scores."""

    class Meta:
        sync_rules = [
            SyncRule("count", from_field="scores", compute=len),
        ]

    player_id = UInt16()
    count = UInt8()
    scores = Array(UInt16(), count=Ref("count"))


def example_arrays():
    """Demonstrate array fields."""
    print("=== Example 3: Arrays ===")

    # Create scoreboard
    board = ScoreBoard(player_id=1234, scores=[100, 250, 180, 320])
    board.sync()
    print(f"Created scoreboard: {board}")
    print(f"  player_id: {board.player_id}")
    print(f"  count: {board.count}")
    print(f"  scores: {board.scores}")

    # Serialize and parse
    raw = board.to_bytes()
    print(f"  Serialized ({len(raw)} bytes): {raw.hex()}")

    parsed = ScoreBoard.parse(raw)
    print(f"  Parsed scores: {parsed.scores}")
    print()


# =============================================================================
# Example 4: Endianness
# =============================================================================


class BigEndianHeader(Struct):
    """Network protocol header (big-endian)."""

    class Meta:
        endian = "big"

    magic = UInt16(default=0xCAFE)
    length = UInt16()
    checksum = UInt32()


class MixedEndianStruct(Struct):
    """Struct with mixed endianness fields."""

    # Default to little-endian
    le_value = UInt32()
    # Override to big-endian for specific field
    be_value = UInt32(endian="big")


def example_endianness():
    """Demonstrate endianness handling."""
    print("=== Example 4: Endianness ===")

    # Big-endian struct
    header = BigEndianHeader(length=256, checksum=0x12345678)
    raw = header.to_bytes()
    print(f"Big-endian header: {raw.hex()}")
    print(f"  magic bytes: {raw[:2].hex()} (0x{header.magic:04X})")
    print(f"  length bytes: {raw[2:4].hex()} (value: {header.length})")

    # Mixed endianness
    mixed = MixedEndianStruct(le_value=0x12345678, be_value=0x12345678)
    raw = mixed.to_bytes()
    print(f"Mixed endian: {raw.hex()}")
    print(f"  LE value: {raw[:4].hex()} (little-endian)")
    print(f"  BE value: {raw[4:].hex()} (big-endian)")
    print()


# =============================================================================
# Example 5: Strings
# =============================================================================


class UserRecord(Struct):
    """User record with string fields."""

    user_id = UInt32()
    name = FixedString(length=20, encoding="utf-8", padding=b"\x00")
    email = FixedString(length=50, encoding="utf-8", padding=b"\x00")


def example_strings():
    """Demonstrate string fields."""
    print("=== Example 5: Strings ===")

    user = UserRecord(
        user_id=42,
        name="Alice",
        email="alice@example.com",
    )
    print(f"User: {user}")
    print(f"  ID: {user.user_id}")
    print(f"  Name: '{user.name}'")
    print(f"  Email: '{user.email}'")

    raw = user.to_bytes()
    print(f"  Total size: {len(raw)} bytes")

    # Parse back
    parsed = UserRecord.parse(raw)
    print(f"  Parsed name: '{parsed.name}'")
    print()


# =============================================================================
# Example 6: Nested Structs
# =============================================================================


class Point(Struct):
    """2D point coordinate."""

    x = Int16()
    y = Int16()


class Rectangle(Struct):
    """Rectangle defined by two points."""

    from pystructs import EmbeddedStruct

    top_left = EmbeddedStruct(Point)
    bottom_right = EmbeddedStruct(Point)


def example_nested():
    """Demonstrate nested struct fields."""
    print("=== Example 6: Nested Structs ===")

    rect = Rectangle(
        top_left=Point(x=10, y=20),
        bottom_right=Point(x=100, y=80),
    )
    print(f"Rectangle: {rect}")
    print(f"  Top-left: ({rect.top_left.x}, {rect.top_left.y})")
    print(f"  Bottom-right: ({rect.bottom_right.x}, {rect.bottom_right.y})")

    raw = rect.to_bytes()
    print(f"  Serialized: {raw.hex()}")

    parsed = Rectangle.parse(raw)
    width = parsed.bottom_right.x - parsed.top_left.x
    height = parsed.bottom_right.y - parsed.top_left.y
    print(f"  Width: {width}, Height: {height}")
    print()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    example_simple_struct()
    example_variable_length()
    example_arrays()
    example_endianness()
    example_strings()
    example_nested()

    print("All examples completed successfully!")
