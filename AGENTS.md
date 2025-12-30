# AGENTS.md - AI Agent Guidelines for pystructs

## Project Overview

**pystructs** is a Django-like declarative binary parsing library for Python. Define binary data structures as classes and parse/serialize them with ease.

### Core Philosophy

- **Zero runtime dependencies** - Pure Python implementation
- **Declarative API** - Define struct layouts as class attributes
- **Bidirectional** - Both parse and serialize binary data
- **Composability** - Structs can be nested with variable-length and conditional fields

### Version & Compatibility

- Current version: 0.4.0
- Python: 3.13+
- No runtime dependencies

---

## Architecture Overview

### Class Hierarchy

```
BaseField (ABC)
├── FixedField (fixed-size fields)
│   ├── IntField → Int8, UInt8, Int16, UInt16, Int32, UInt32, Int64, UInt64
│   ├── FloatField → Float32, Float64
│   ├── FixedBytes
│   ├── FixedString
│   └── Bool
├── Bytes (variable-size, uses Ref)
├── String, NullTerminatedString
├── Array (repeated fields)
├── EmbeddedStruct (nested structs)
├── Conditional (optional fields based on condition)
├── Switch (tagged unions)
├── Padding, Flags, Enum (special fields)
└── BitField → Bit, Bits (bit-level parsing)

Struct (metaclass=StructMeta)
└── User-defined structs

BitStruct (metaclass=BitStructMeta)
└── User-defined bit-level structs
```

### Design Patterns in Use

1. **Descriptor Protocol** - Fields implement `__get__`/`__set__` for attribute access
2. **Metaclass** - `StructMeta` collects field definitions and processes `class Meta`
3. **Composite** - `Struct` contains multiple `BaseField` instances
4. **Reference System** - `Ref` class enables cross-field references

### Key Abstractions

| Class | Purpose | Location |
|-------|---------|----------|
| `BaseField` | Abstract base for all fields | `pystructs/base.py` |
| `FixedField` | Base for fixed-size fields | `pystructs/base.py` |
| `Struct` | Base class for binary structures | `pystructs/struct.py` |
| `StructMeta` | Metaclass that collects fields | `pystructs/struct.py` |
| `Ref` | Reference to another field's value | `pystructs/ref.py` |
| `SyncRule` | Automatic field synchronization | `pystructs/sync.py` |
| `BitStruct` | Bit-level structure | `pystructs/fields/bitfields.py` |

---

## Code Structure

```
pystructs/
├── pystructs/
│   ├── __init__.py              # Public API exports
│   ├── base.py                  # BaseField, FixedField
│   ├── struct.py                # Struct, StructMeta, StructOptions
│   ├── ref.py                   # Ref, RefComparison, RefLogical
│   ├── sync.py                  # SyncRule
│   ├── validate.py              # Validators (Range, OneOf, etc.)
│   ├── expressions.py           # Len, Value, Const, Checksum
│   ├── exceptions.py            # Exception hierarchy
│   ├── config.py                # Global configuration
│   └── fields/
│       ├── __init__.py          # Re-exports all field types
│       ├── integers.py          # Int8, UInt8, Int16, UInt16, etc.
│       ├── floats.py            # Float32, Float64
│       ├── bytes_fields.py      # FixedBytes, Bytes
│       ├── strings.py           # FixedString, String, NullTerminatedString
│       ├── composite.py         # Array, EmbeddedStruct, Conditional, Switch
│       ├── special.py           # Bool, Padding, Flags, Enum
│       └── bitfields.py         # Bit, Bits, BitStruct, EmbeddedBitStruct
├── tests/
│   ├── test_struct.py
│   ├── test_ref.py
│   ├── test_sync.py
│   ├── test_validate.py
│   ├── test_expressions.py
│   └── fields/
│       ├── test_integers.py
│       ├── test_floats.py
│       ├── test_bytes.py
│       ├── test_strings.py
│       ├── test_composite.py
│       ├── test_special.py
│       └── test_bitfields.py
├── examples/
│   ├── basic_usage.py           # Basic usage examples
│   ├── tcp_packet.py            # TCP packet parsing with BitStruct
│   ├── stun_message.py          # STUN protocol example
│   └── advanced_features.py     # Conditional, Switch, Validation
└── docs/                        # Sphinx documentation
```

---

## Key Conventions

### Import Style

```python
# Direct imports (recommended)
from pystructs import Struct, UInt8, UInt16, Bytes, Ref

# Or import specific modules
from pystructs.fields import integers, composite
from pystructs import validate
```

### Struct Definition Pattern

```python
from pystructs import Struct, UInt8, UInt16, Bytes, Ref, SyncRule

class Packet(Struct):
    class Meta:
        endian = "big"  # or "little" (default)
        sync_rules = [
            SyncRule("length", from_field="data", compute=len),
        ]

    header = UInt8(default=0xFF)
    length = UInt16()
    data = Bytes(size=Ref("length"))

# Parse from bytes
packet = Packet.parse(raw_bytes)
value = packet.header  # Direct attribute access

# Create and serialize
new_packet = Packet(header=0xAB, data=b"Hello")
new_packet.sync()  # Apply sync rules
raw = new_packet.to_bytes()
```

### Field Definition Pattern

All new field types should:

1. Inherit from `BaseField` (or `FixedField` for fixed-size)
2. Implement `get_size(instance)` method
3. Implement `parse(buffer, instance)` method
4. Implement `serialize(value, instance)` method

```python
from pystructs.base import FixedField

class NewField(FixedField):
    size = 4  # Fixed size in bytes

    def __init__(self, default=None, required=True, validators=None):
        super().__init__(default=default, required=required, validators=validators)

    def parse(self, buffer: BinaryIO, instance: Struct) -> Any:
        data = buffer.read(self.size)
        return transform(data)

    def serialize(self, value: Any, instance: Struct) -> bytes:
        return to_bytes(value)
```

### Variable-Length Fields with Ref

Use `Ref` to reference other fields:

```python
class Packet(Struct):
    length = UInt16()
    data = Bytes(size=Ref("length"))  # Size from length field
    count = UInt8()
    items = Array(UInt32(), count=Ref("count"))  # Count from field
```

### Conditional Fields

```python
class Message(Struct):
    version = UInt8()
    # Only present when version >= 2
    extra = Conditional(UInt32(), when=Ref("version") >= 2)
```

### `__all__` Tuple Convention

All modules define `__all__` as a tuple (not list) for exports:

```python
__all__ = (
    "ClassName1",
    "ClassName2",
)
```

---

## Development Workflow

### Setup

```bash
# Using uv (recommended)
pip install uv
uv sync --dev

# Or install dev dependencies directly
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest --cov-report term --cov pystructs tests

# Run specific test file
pytest tests/fields/test_integers.py

# Run specific test
pytest tests/test_struct.py::test_parse_simple_struct
```

### Code Formatting

Ruff is enforced via GitHub Actions:

```bash
# Check formatting
ruff format --check .

# Apply formatting
ruff format .

# Check linting
ruff check .

# Fix linting issues
ruff check --fix .
```

### Test Writing Pattern

```python
import pytest
from pystructs import Struct, UInt8, UInt16

def test_parse_simple_struct():
    class Simple(Struct):
        value = UInt8()

    result = Simple.parse(b"\x42")
    assert result.value == 0x42

def test_serialize_struct():
    class Simple(Struct):
        value = UInt8(default=0x42)

    s = Simple()
    assert s.to_bytes() == b"\x42"
```

---

## Important Files Reference

| File | Role | When to Modify |
|------|------|----------------|
| `pystructs/base.py` | BaseField, FixedField classes | Adding new field base types |
| `pystructs/struct.py` | Struct, StructMeta, parse/serialize | Core parsing logic changes |
| `pystructs/ref.py` | Ref, RefComparison | Field reference system |
| `pystructs/sync.py` | SyncRule | Synchronization logic |
| `pystructs/validate.py` | Validators | Adding new validators |
| `pystructs/__init__.py` | Public API exports | Adding new public types |
| `pystructs/fields/__init__.py` | Field re-exports | Adding new field types |

---

## Guidelines for Making Changes

### Adding a New Field Type

1. Create or modify file in `pystructs/fields/`
2. Inherit from `BaseField` or `FixedField`
3. Implement `get_size()`, `parse()`, `serialize()` methods
4. Define `__all__` tuple with exported classes
5. Add import to `pystructs/fields/__init__.py`
6. Add to `__all__` in `pystructs/__init__.py`
7. Create tests in `tests/fields/`
8. Run `ruff format .` and `ruff check --fix .` for formatting

### Modifying Existing Behavior

1. Check existing tests to understand expected behavior
2. Write new tests for changed/added behavior FIRST
3. Make minimal changes to implementation
4. Ensure all tests pass: `pytest tests/`
5. Format code: `ruff format .` and `ruff check --fix .`

### Common Pitfalls to Avoid

1. **Forgetting sync()** - Call `sync()` before `to_bytes()` when using SyncRule
2. **Circular imports** - Use `TYPE_CHECKING` guard for type hints:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from pystructs.struct import Struct
   ```
3. **Endianness** - Default is little-endian; use `class Meta: endian = "big"` for network protocols
4. **Ref paths** - Use `.` for nested fields, `../` for parent, `/` for absolute paths

### Testing Checklist

- [ ] Test parsing from bytes
- [ ] Test serialization to bytes
- [ ] Test round-trip (parse → to_bytes → parse)
- [ ] Test with different endianness
- [ ] Test edge cases (empty data, boundary values)
- [ ] Test validation if applicable
- [ ] Test sync rules if applicable

---

## CI/CD Information

- **GitHub Actions**: Runs pytest with coverage on Python 3.13, 3.14
- **GitHub Actions**: Runs Ruff linting and formatting checks on push/PR
- **Codecov**: Coverage reporting
- **Read the Docs**: Documentation hosting
- **PyPI**: Deployment on tagged releases (main branch)
