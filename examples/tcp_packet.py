#!/usr/bin/env python3
"""TCP Packet parsing example using pystructs.

This module demonstrates parsing and creating TCP packets according to
RFC 793 (https://datatracker.ietf.org/doc/html/rfc793).

TCP Header Format:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          Source Port          |       Destination Port        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Sequence Number                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Acknowledgment Number                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Data |           |U|A|P|R|S|F|                               |
   | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
   |       |           |G|K|H|T|N|N|                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           Checksum            |         Urgent Pointer        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                             data                              |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""

from pystructs import (
    Bit,
    Bits,
    BitStruct,
    EmbeddedBitStruct,
    Struct,
    UInt16,
    UInt32,
)

# =============================================================================
# TCP Flags using BitStruct
# =============================================================================


class TCPFlags(BitStruct):
    """TCP control flags (6 bits).

    Bit layout (LSB first):
        FIN (bit 0): No more data from sender
        SYN (bit 1): Synchronize sequence numbers
        RST (bit 2): Reset the connection
        PSH (bit 3): Push function
        ACK (bit 4): Acknowledgment field significant
        URG (bit 5): Urgent pointer field significant
    """

    class Meta:
        size = 1  # 8 bits, but only 6 used

    fin = Bit()
    syn = Bit()
    rst = Bit()
    psh = Bit()
    ack = Bit()
    urg = Bit()
    reserved = Bits(2)  # Reserved bits


class TCPDataOffsetFlags(BitStruct):
    """Combined data offset and flags byte.

    Layout (8 bits):
        Lower 4 bits: Reserved/NS flag
        Upper 4 bits: Data offset (header length in 32-bit words)
    """

    class Meta:
        size = 1

    reserved_ns = Bits(4)
    data_offset = Bits(4)


# =============================================================================
# TCP Header
# =============================================================================


class TCPHeader(Struct):
    """TCP Header structure.

    Note: This is a simplified version. The actual TCP header has
    variable-length options which would require more complex handling.

    Attributes:
        src_port: Source port number (16 bits)
        dst_port: Destination port number (16 bits)
        seq_num: Sequence number (32 bits)
        ack_num: Acknowledgment number (32 bits)
        data_offset_flags: Data offset and reserved bits
        flags: TCP control flags
        window: Window size (16 bits)
        checksum: Header checksum (16 bits)
        urgent_ptr: Urgent pointer (16 bits)
    """

    class Meta:
        endian = "big"  # Network byte order

    src_port = UInt16()
    dst_port = UInt16()
    seq_num = UInt32()
    ack_num = UInt32()
    data_offset_flags = EmbeddedBitStruct(TCPDataOffsetFlags)
    flags = EmbeddedBitStruct(TCPFlags)
    window = UInt16()
    checksum = UInt16()
    urgent_ptr = UInt16()


class TCPSegment(Struct):
    """Complete TCP segment with header and payload.

    The payload size is calculated from the total IP packet length
    minus the IP header length minus the TCP header length.
    For this example, we use a fixed payload size.
    """

    class Meta:
        endian = "big"
        trailing_data = "ignore"

    header = TCPHeader()  # Will be wrapped in EmbeddedStruct by metaclass
    # Note: In real implementation, payload size would come from IP layer


# =============================================================================
# Helper Functions
# =============================================================================


def create_syn_packet(src_port: int, dst_port: int, seq_num: int) -> TCPHeader:
    """Create a TCP SYN packet for connection initiation."""
    return TCPHeader(
        src_port=src_port,
        dst_port=dst_port,
        seq_num=seq_num,
        ack_num=0,
        data_offset_flags=TCPDataOffsetFlags(data_offset=5),  # 20 bytes (5 * 4)
        flags=TCPFlags(syn=True),
        window=65535,
        checksum=0,  # Would be calculated
        urgent_ptr=0,
    )


def create_syn_ack_packet(
    src_port: int, dst_port: int, seq_num: int, ack_num: int
) -> TCPHeader:
    """Create a TCP SYN-ACK packet for connection response."""
    return TCPHeader(
        src_port=src_port,
        dst_port=dst_port,
        seq_num=seq_num,
        ack_num=ack_num,
        data_offset_flags=TCPDataOffsetFlags(data_offset=5),
        flags=TCPFlags(syn=True, ack=True),
        window=65535,
        checksum=0,
        urgent_ptr=0,
    )


def create_ack_packet(
    src_port: int, dst_port: int, seq_num: int, ack_num: int
) -> TCPHeader:
    """Create a TCP ACK packet."""
    return TCPHeader(
        src_port=src_port,
        dst_port=dst_port,
        seq_num=seq_num,
        ack_num=ack_num,
        data_offset_flags=TCPDataOffsetFlags(data_offset=5),
        flags=TCPFlags(ack=True),
        window=65535,
        checksum=0,
        urgent_ptr=0,
    )


def print_tcp_header(header: TCPHeader, title: str = "TCP Header"):
    """Pretty print a TCP header."""
    print(f"\n{title}")
    print("=" * 60)
    print(f"  Source Port:      {header.src_port}")
    print(f"  Destination Port: {header.dst_port}")
    print(f"  Sequence Number:  {header.seq_num}")
    print(f"  Ack Number:       {header.ack_num}")
    data_offset = header.data_offset_flags.data_offset
    print(f"  Data Offset:      {data_offset} ({data_offset * 4} bytes)")
    print("  Flags:            ", end="")
    flags = []
    if header.flags.urg:
        flags.append("URG")
    if header.flags.ack:
        flags.append("ACK")
    if header.flags.psh:
        flags.append("PSH")
    if header.flags.rst:
        flags.append("RST")
    if header.flags.syn:
        flags.append("SYN")
    if header.flags.fin:
        flags.append("FIN")
    print(", ".join(flags) if flags else "(none)")
    print(f"  Window:           {header.window}")
    print(f"  Checksum:         0x{header.checksum:04X}")
    print(f"  Urgent Pointer:   {header.urgent_ptr}")


# =============================================================================
# Demo: TCP Three-Way Handshake
# =============================================================================


def demo_tcp_handshake():
    """Demonstrate TCP three-way handshake packet creation."""
    print("\n" + "=" * 60)
    print("TCP Three-Way Handshake Demonstration")
    print("=" * 60)

    # Client -> Server: SYN
    syn = create_syn_packet(
        src_port=54321,
        dst_port=80,
        seq_num=1000,
    )
    print_tcp_header(syn, "Step 1: Client -> Server (SYN)")
    syn_bytes = syn.to_bytes()
    print(f"  Raw bytes ({len(syn_bytes)}): {syn_bytes.hex()}")

    # Server -> Client: SYN-ACK
    syn_ack = create_syn_ack_packet(
        src_port=80,
        dst_port=54321,
        seq_num=2000,
        ack_num=1001,  # Client's seq + 1
    )
    print_tcp_header(syn_ack, "Step 2: Server -> Client (SYN-ACK)")
    syn_ack_bytes = syn_ack.to_bytes()
    print(f"  Raw bytes ({len(syn_ack_bytes)}): {syn_ack_bytes.hex()}")

    # Client -> Server: ACK
    ack = create_ack_packet(
        src_port=54321,
        dst_port=80,
        seq_num=1001,
        ack_num=2001,  # Server's seq + 1
    )
    print_tcp_header(ack, "Step 3: Client -> Server (ACK)")
    ack_bytes = ack.to_bytes()
    print(f"  Raw bytes ({len(ack_bytes)}): {ack_bytes.hex()}")

    print("\nConnection established!")


def demo_parse_tcp_packet():
    """Demonstrate parsing a raw TCP packet."""
    print("\n" + "=" * 60)
    print("TCP Packet Parsing Demonstration")
    print("=" * 60)

    # Raw TCP SYN packet (HTTP port 80)
    raw_packet = bytes(
        [
            0xD4,
            0x31,  # Source port: 54321
            0x00,
            0x50,  # Destination port: 80
            0x00,
            0x00,
            0x03,
            0xE8,  # Sequence number: 1000
            0x00,
            0x00,
            0x00,
            0x00,  # Ack number: 0
            0x50,  # Data offset: 5 (20 bytes), reserved: 0
            0x02,  # Flags: SYN only
            0xFF,
            0xFF,  # Window: 65535
            0x00,
            0x00,  # Checksum: 0 (not calculated)
            0x00,
            0x00,  # Urgent pointer: 0
        ]
    )

    print(f"Raw packet ({len(raw_packet)} bytes): {raw_packet.hex()}")

    # Parse the packet
    header = TCPHeader.parse(raw_packet)
    print_tcp_header(header, "Parsed TCP Header")

    # Verify round-trip
    reserialized = header.to_bytes()
    print(f"\nReserialized: {reserialized.hex()}")
    print(f"Round-trip OK: {raw_packet == reserialized}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    demo_tcp_handshake()
    demo_parse_tcp_packet()

    print("\n" + "=" * 60)
    print("TCP packet examples completed successfully!")
    print("=" * 60)
