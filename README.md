# pystructs

[![Documentation Status](https://readthedocs.org/projects/pystructs/badge/?version=latest)](https://pystructs.readthedocs.io/en/latest/?badge=latest)
[![CI](https://github.com/moreal/pystructs/actions/workflows/ci.yml/badge.svg)](https://github.com/moreal/pystructs/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/moreal/pystructs/branch/main/graph/badge.svg)](https://codecov.io/gh/moreal/pystructs)

**pystructs** is a Django-like declarative binary parsing library for Python. Define binary data structures as classes and parse/serialize them with ease.

## Features

- **Declarative syntax** - Define structs like Django models
- **Bidirectional** - Parse binary data and serialize back to bytes
- **Rich field types** - Integers, floats, bytes, strings, arrays, and more
- **Bit-level parsing** - `BitStruct` for parsing individual bits
- **Conditional fields** - Fields that exist based on runtime conditions
- **Validation system** - Built-in and custom validators
- **Zero runtime dependencies** - Pure Python implementation

## Installation

```bash
pip install pystructs
uv add pystructs
```

## Quick Start

```python
from pystructs import Struct, UInt8, UInt16, UInt32, Bytes, Ref, SyncRule

class Packet(Struct):
    class Meta:
        endian = "big"
        sync_rules = [
            SyncRule("length", from_field="payload", compute=len),
        ]

    magic = UInt32(default=0xDEADBEEF)
    version = UInt8(default=1)
    length = UInt16()
    payload = Bytes(size=Ref("length"))

# Parse from bytes
data = b"\xde\xad\xbe\xef\x01\x00\x05Hello"
packet = Packet.parse(data)
print(packet.magic)    # 3735928559 (0xDEADBEEF)
print(packet.version)  # 1
print(packet.payload)  # b'Hello'

# Create and serialize
new_packet = Packet(payload=b"World")
new_packet.sync()  # Auto-calculate length
print(new_packet.to_bytes())
```

## More Examples

### Variable-Length Arrays

```python
from pystructs import Struct, UInt8, UInt16, Array, Ref, SyncRule

class ScoreBoard(Struct):
    class Meta:
        sync_rules = [
            SyncRule("count", from_field="scores", compute=len),
        ]

    player_id = UInt16()
    count = UInt8()
    scores = Array(UInt16(), count=Ref("count"))

board = ScoreBoard(player_id=1234, scores=[100, 250, 180])
board.sync()
print(board.to_bytes())  # Serializes with count=3
```

### Bit-Level Parsing

```python
from pystructs import Struct, UInt16, BitStruct, Bit, Bits, EmbeddedBitStruct

class TCPFlags(BitStruct):
    class Meta:
        size = 1

    fin = Bit()
    syn = Bit()
    rst = Bit()
    psh = Bit()
    ack = Bit()
    urg = Bit()
    reserved = Bits(2)

class TCPHeader(Struct):
    class Meta:
        endian = "big"

    src_port = UInt16()
    dst_port = UInt16()
    flags = EmbeddedBitStruct(TCPFlags)

header = TCPHeader.parse(b"\x00\x50\x1f\x90\x12")
print(header.src_port)     # 80
print(header.flags.syn)    # True
```

### Conditional Fields

```python
from pystructs import Struct, UInt8, UInt32, Conditional, Ref

class VersionedPacket(Struct):
    version = UInt8()
    # Only present in version 2+
    extended_header = Conditional(
        UInt32(),
        when=Ref("version") >= 2,
    )
    data = UInt8()

# Version 1: no extended header
v1 = VersionedPacket.parse(b"\x01\x42")
print(v1.extended_header)  # None

# Version 2: with extended header
v2 = VersionedPacket.parse(b"\x02\x00\x00\x00\x01\x42")
print(v2.extended_header)  # 1
```

### Tagged Unions (Switch)

```python
from pystructs import Struct, UInt8, UInt16, UInt32, Switch, Ref

class TextPayload(Struct):
    length = UInt8()
    # text would use Bytes(size=Ref("length"))

class BinaryPayload(Struct):
    size = UInt16()
    # data would use Bytes(size=Ref("size"))

class Message(Struct):
    msg_type = UInt8()
    payload = Switch(
        discriminator=Ref("msg_type"),
        cases={
            1: TextPayload,
            2: BinaryPayload,
        },
    )
```

## Field Types

| Category | Fields |
|----------|--------|
| **Integers** | `Int8`, `UInt8`, `Int16`, `UInt16`, `Int32`, `UInt32`, `Int64`, `UInt64` |
| **Floats** | `Float32`, `Float64` |
| **Bytes** | `FixedBytes`, `Bytes` |
| **Strings** | `FixedString`, `String`, `NullTerminatedString` |
| **Composite** | `Array`, `EmbeddedStruct`, `Conditional`, `Switch` |
| **Special** | `Bool`, `Padding`, `Flags`, `Enum` |
| **Bit-level** | `BitStruct`, `Bit`, `Bits`, `EmbeddedBitStruct` |

## Documentation

Full documentation is available at [Read the Docs](https://pystructs.readthedocs.io/).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and contribution guidelines.

## License

MIT License
