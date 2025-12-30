#!/usr/bin/env python3
"""STUN Message parsing example using pystructs.

This module demonstrates parsing and creating STUN (Session Traversal
Utilities for NAT) messages according to RFC 5389.
https://datatracker.ietf.org/doc/html/rfc5389

STUN Message Format:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |0 0|     STUN Message Type     |         Message Length        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Magic Cookie                          |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   |                     Transaction ID (96 bits)                  |
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

STUN Attribute Format:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         Type                  |            Length             |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Value (variable)                ....
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""

import os
from enum import IntEnum
from typing import Optional

from pystructs import (
    Bytes,
    FixedBytes,
    Ref,
    Struct,
    UInt8,
    UInt16,
    UInt32,
)

# =============================================================================
# STUN Constants
# =============================================================================

# Magic cookie value (RFC 5389)
STUN_MAGIC_COOKIE = 0x2112A442


class STUNMessageType(IntEnum):
    """STUN message types (RFC 5389)."""

    # Binding methods
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101
    BINDING_ERROR_RESPONSE = 0x0111
    BINDING_INDICATION = 0x0011


class STUNAttributeType(IntEnum):
    """STUN attribute types (RFC 5389)."""

    # Comprehension-required range (0x0000-0x7FFF)
    MAPPED_ADDRESS = 0x0001
    USERNAME = 0x0006
    MESSAGE_INTEGRITY = 0x0008
    ERROR_CODE = 0x0009
    UNKNOWN_ATTRIBUTES = 0x000A
    REALM = 0x0014
    NONCE = 0x0015
    XOR_MAPPED_ADDRESS = 0x0020

    # Comprehension-optional range (0x8000-0xFFFF)
    SOFTWARE = 0x8022
    ALTERNATE_SERVER = 0x8023
    FINGERPRINT = 0x8028


class AddressFamily(IntEnum):
    """Address family for MAPPED-ADDRESS."""

    IPV4 = 0x01
    IPV6 = 0x02


# =============================================================================
# STUN Structures
# =============================================================================


class STUNHeader(Struct):
    """STUN message header (20 bytes).

    Attributes:
        message_type: STUN message type (2 bytes)
        message_length: Length of message after header (2 bytes)
        magic_cookie: Magic cookie (0x2112A442)
        transaction_id: Unique transaction identifier (12 bytes)
    """

    class Meta:
        endian = "big"

    message_type = UInt16()
    message_length = UInt16()
    magic_cookie = UInt32(default=STUN_MAGIC_COOKIE)
    transaction_id = FixedBytes(length=12)


class STUNAttribute(Struct):
    """Generic STUN attribute.

    Attributes:
        attr_type: Attribute type (2 bytes)
        length: Value length (2 bytes)
        value: Attribute value (variable length)

    Note: Attributes must be padded to 4-byte boundary
    """

    class Meta:
        endian = "big"

    attr_type = UInt16()
    length = UInt16()
    value = Bytes(size=Ref("length"))


class MappedAddressValue(Struct):
    """Value format for MAPPED-ADDRESS attribute.

    Format:
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |0 0 0 0 0 0 0 0|    Family     |           Port                |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                                                               |
       |                 Address (32 bits or 128 bits)                 |
       |                                                               |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """

    class Meta:
        endian = "big"

    reserved = UInt8(default=0)
    family = UInt8()
    port = UInt16()
    address = FixedBytes(length=4)  # IPv4 only in this example


class XORMappedAddressValue(Struct):
    """Value format for XOR-MAPPED-ADDRESS attribute.

    X-Port is computed by XOR'ing the mapped port with the most significant
    16 bits of the magic cookie.

    X-Address (IPv4) is computed by XOR'ing the mapped IP address with the
    magic cookie.
    """

    class Meta:
        endian = "big"

    reserved = UInt8(default=0)
    family = UInt8()
    x_port = UInt16()
    x_address = FixedBytes(length=4)  # IPv4 only


class ErrorCodeValue(Struct):
    """Value format for ERROR-CODE attribute.

    Format:
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |           Reserved, should be 0         |Class|     Number    |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |      Reason Phrase (variable)                                ..
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """

    class Meta:
        endian = "big"

    reserved = UInt16(default=0)
    error_class = UInt8()  # 3 bits (0-7), but stored as byte
    error_number = UInt8()  # 0-99


# =============================================================================
# Helper Functions
# =============================================================================


def generate_transaction_id() -> bytes:
    """Generate a random 96-bit transaction ID."""
    return os.urandom(12)


def xor_address(
    ip_bytes: bytes, port: int, magic_cookie: int = STUN_MAGIC_COOKIE
) -> tuple:
    """XOR an address with the magic cookie.

    Args:
        ip_bytes: IPv4 address as 4 bytes
        port: Port number
        magic_cookie: STUN magic cookie

    Returns:
        Tuple of (x_address_bytes, x_port)
    """
    # XOR port with most significant 16 bits of magic cookie
    x_port = port ^ (magic_cookie >> 16)

    # XOR IP address with magic cookie
    magic_bytes = magic_cookie.to_bytes(4, "big")
    x_address = bytes(a ^ b for a, b in zip(ip_bytes, magic_bytes))

    return x_address, x_port


def decode_xor_address(
    x_ip_bytes: bytes, x_port: int, magic_cookie: int = STUN_MAGIC_COOKIE
) -> tuple:
    """Decode an XOR'd address.

    Args:
        x_ip_bytes: XOR'd IPv4 address
        x_port: XOR'd port
        magic_cookie: STUN magic cookie

    Returns:
        Tuple of (ip_string, port)
    """
    # Decode port
    port = x_port ^ (magic_cookie >> 16)

    # Decode IP
    magic_bytes = magic_cookie.to_bytes(4, "big")
    ip_bytes = bytes(a ^ b for a, b in zip(x_ip_bytes, magic_bytes))
    ip_string = ".".join(str(b) for b in ip_bytes)

    return ip_string, port


def create_binding_request(transaction_id: Optional[bytes] = None) -> bytes:
    """Create a STUN Binding Request message.

    Args:
        transaction_id: Optional transaction ID (random if not provided)

    Returns:
        Raw bytes of the STUN message
    """
    if transaction_id is None:
        transaction_id = generate_transaction_id()

    header = STUNHeader(
        message_type=STUNMessageType.BINDING_REQUEST,
        message_length=0,  # No attributes
        transaction_id=transaction_id,
    )

    return header.to_bytes()


def create_binding_response(
    transaction_id: bytes,
    mapped_ip: str,
    mapped_port: int,
) -> bytes:
    """Create a STUN Binding Response message with XOR-MAPPED-ADDRESS.

    Args:
        transaction_id: Transaction ID from the request
        mapped_ip: Mapped IP address (e.g., "192.168.1.1")
        mapped_port: Mapped port number

    Returns:
        Raw bytes of the STUN message
    """
    # Convert IP string to bytes
    ip_parts = [int(p) for p in mapped_ip.split(".")]
    ip_bytes = bytes(ip_parts)

    # XOR the address
    x_address, x_port = xor_address(ip_bytes, mapped_port)

    # Create XOR-MAPPED-ADDRESS attribute value
    addr_value = XORMappedAddressValue(
        family=AddressFamily.IPV4,
        x_port=x_port,
        x_address=x_address,
    )
    addr_value_bytes = addr_value.to_bytes()

    # Create attribute
    attr = STUNAttribute(
        attr_type=STUNAttributeType.XOR_MAPPED_ADDRESS,
        length=len(addr_value_bytes),
        value=addr_value_bytes,
    )
    attr_bytes = attr.to_bytes()

    # Pad to 4-byte boundary
    padding_needed = (4 - (len(attr_bytes) % 4)) % 4
    attr_bytes += b"\x00" * padding_needed

    # Create header
    header = STUNHeader(
        message_type=STUNMessageType.BINDING_RESPONSE,
        message_length=len(attr_bytes),
        transaction_id=transaction_id,
    )

    return header.to_bytes() + attr_bytes


def parse_stun_message(data: bytes) -> dict:
    """Parse a STUN message.

    Args:
        data: Raw STUN message bytes

    Returns:
        Dictionary with parsed message information
    """
    result = {}

    # Parse header
    header = STUNHeader.parse(data[:20])
    result["message_type"] = STUNMessageType(header.message_type)
    result["message_length"] = header.message_length
    result["magic_cookie"] = f"0x{header.magic_cookie:08X}"
    result["transaction_id"] = header.transaction_id.hex()

    # Parse attributes
    result["attributes"] = []
    offset = 20
    while offset < 20 + header.message_length:
        attr = STUNAttribute.parse(data[offset:])
        attr_info = {
            "type": f"0x{attr.attr_type:04X}",
            "length": attr.length,
            "value_hex": attr.value.hex(),
        }

        # Try to identify known attribute types
        try:
            attr_info["type_name"] = STUNAttributeType(attr.attr_type).name
        except ValueError:
            attr_info["type_name"] = "UNKNOWN"

        # Parse XOR-MAPPED-ADDRESS
        if attr.attr_type == STUNAttributeType.XOR_MAPPED_ADDRESS:
            xma = XORMappedAddressValue.parse(attr.value)
            ip, port = decode_xor_address(xma.x_address, xma.x_port)
            attr_info["decoded"] = {"ip": ip, "port": port}

        result["attributes"].append(attr_info)

        # Move to next attribute (with padding)
        attr_size = 4 + attr.length
        padding = (4 - (attr_size % 4)) % 4
        offset += attr_size + padding

    return result


def print_stun_message(data: bytes, title: str = "STUN Message"):
    """Pretty print a parsed STUN message."""
    parsed = parse_stun_message(data)

    print(f"\n{title}")
    print("=" * 60)
    msg_type = parsed["message_type"]
    print(f"  Message Type:    {msg_type.name} (0x{msg_type.value:04X})")
    print(f"  Message Length:  {parsed['message_length']} bytes")
    print(f"  Magic Cookie:    {parsed['magic_cookie']}")
    print(f"  Transaction ID:  {parsed['transaction_id']}")

    if parsed["attributes"]:
        print("\n  Attributes:")
        for attr in parsed["attributes"]:
            print(f"    - {attr['type_name']} ({attr['type']})")
            print(f"      Length: {attr['length']}")
            print(f"      Value:  {attr['value_hex']}")
            if "decoded" in attr:
                print(
                    f"      Decoded: {attr['decoded']['ip']}:{attr['decoded']['port']}"
                )


# =============================================================================
# Demo
# =============================================================================


def demo_stun_binding():
    """Demonstrate STUN Binding Request/Response."""
    print("\n" + "=" * 60)
    print("STUN Binding Request/Response Demonstration")
    print("=" * 60)

    # Generate a transaction ID
    transaction_id = generate_transaction_id()
    print(f"\nTransaction ID: {transaction_id.hex()}")

    # Create Binding Request
    request = create_binding_request(transaction_id)
    print(f"\nBinding Request ({len(request)} bytes): {request.hex()}")
    print_stun_message(request, "Binding Request")

    # Simulate receiving a response with mapped address
    mapped_ip = "203.0.113.42"
    mapped_port = 54321

    response = create_binding_response(transaction_id, mapped_ip, mapped_port)
    print(f"\nBinding Response ({len(response)} bytes): {response.hex()}")
    print_stun_message(response, "Binding Response")

    print(f"\n  -> Your public address: {mapped_ip}:{mapped_port}")


def demo_parse_real_stun():
    """Parse a real STUN message capture."""
    print("\n" + "=" * 60)
    print("Parsing Real STUN Message")
    print("=" * 60)

    # Real STUN Binding Request captured from network
    # (20 bytes, no attributes)
    real_request = bytes(
        [
            0x00,
            0x01,  # Message type: Binding Request
            0x00,
            0x00,  # Message length: 0
            0x21,
            0x12,
            0xA4,
            0x42,  # Magic cookie
            # Transaction ID (12 bytes)
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
        ]
    )

    print(f"\nReal STUN request: {real_request.hex()}")
    print_stun_message(real_request, "Parsed Real Request")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    demo_stun_binding()
    demo_parse_real_stun()

    print("\n" + "=" * 60)
    print("STUN message examples completed successfully!")
    print("=" * 60)
