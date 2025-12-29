# AGENTS.md - AI Agent Guidelines for pystructs

## Project Overview

**pystructs** is a Python package providing C-like struct implementation for binary data parsing. It enables declarative definition of binary data structures and automatic parsing of byte streams.

### Core Philosophy

- **Zero runtime dependencies** - No external packages required at runtime
- **Declarative API** - Define struct layouts as class attributes
- **Automatic offset calculation** - Fields are linked and offsets computed automatically
- **Composability** - Structs can be nested and combined with variable-length fields

### Version & Compatibility

- Current version: 0.3.0
- Python: 3.9+
- No runtime dependencies

---

## Architecture Overview

### Class Hierarchy

```
Field (abstract base)
├── BytesField (concrete, reads raw bytes)
│   ├── IntField (converts bytes to int)
│   │   ├── Int8Field, Int16Field, Int32Field, Int64Field
│   ├── StringField (converts bytes to string)
│   └── Struct (composite field with nested fields)
│       └── MultipleField (array of fields)
└── VariableBytesField (variable-length data)
```

### Design Patterns in Use

1. **Template Method** - `Field.fetch()` and `Field.initialize()` define the contract
2. **Metaclass** - `StructMetaclass` automatically registers class attributes as fields
3. **Composite** - `Struct` contains multiple `Field` instances
4. **Lazy Initialization** - Fields compute values on `fetch()` call, not construction
5. **Linked List** - Fields maintain `prev` references for offset calculation

### Key Abstractions

| Class | Purpose | Location |
|-------|---------|----------|
| `Field` | Abstract base defining `fetch()`, `initialize()`, `offset`, `size` | `pystructs/fields/field.py` |
| `BytesField` | Concrete field reading raw bytes from buffer | `pystructs/fields/bytes.py` |
| `Struct` | Composite field with automatic field linking | `pystructs/fields/struct.py` |
| `StructMetaclass` | Extracts Field attributes into `fields` dict | `pystructs/fields/struct.py` |
| `VariableBytesField` | Dynamic-size field referencing another field for length | `pystructs/fields/variable.py` |
| `MultipleField` | Array/list of repeated fields | `pystructs/fields/multiple.py` |

---

## Code Structure

```
pystructs/
├── pystructs/                    # Main package
│   ├── __init__.py              # Re-exports from fields
│   ├── utils.py                 # Utilities: deepattr, filter_fields, delete_fields
│   └── fields/
│       ├── __init__.py          # Exports all field types
│       ├── field.py             # Field abstract base class
│       ├── bytes.py             # BytesField implementation
│       ├── struct.py            # Struct and StructMetaclass
│       ├── integer.py           # IntField and sized variants
│       ├── string.py            # StringField
│       ├── variable.py          # VariableBytesField
│       └── multiple.py          # MultipleField
├── tests/
│   └── fields/                  # Mirror structure of source
│       ├── test_bytes.py
│       ├── test_field.py
│       ├── test_integer.py
│       ├── test_multiple.py
│       ├── test_string.py
│       ├── test_struct.py
│       └── test_variable.py
├── examples/
│   └── stun_message.py          # STUN protocol parsing example
└── docs/                        # Sphinx documentation
```

---

## Key Conventions

### Import Style

```python
# Use relative imports within package
from pystructs.fields import BytesField, Field
from pystructs import utils

# External usage
from pystructs import fields
# or
from pystructs.fields import Struct, BytesField, Int32Field
```

### Field Definition Pattern

All new field types should:

1. Inherit from `BytesField` (or `Field` for non-byte-backed fields)
2. Override `fetch()` to return the parsed value
3. Optionally override `initialize()` for setup logic
4. Define `size` property if variable-length

```python
class NewField(BytesField):
    def __init__(self, size: int, custom_param):
        super().__init__(size)
        self.custom_param = custom_param

    def fetch(self) -> ReturnType:
        raw = super().fetch()  # Get bytes
        return transform(raw)  # Return parsed value
```

### Struct Definition Pattern

```python
class MyStruct(fields.Struct):
    field_a = fields.BytesField(size=4)
    field_b = fields.Int32Field(byteorder='big')
    # Fields are processed in definition order

# Usage
struct = MyStruct(binary_data)
struct.initialize()  # Links fields and sets up parsing
value = struct.field_a  # Calls field_a.fetch()
```

### Variable-Length Fields

Use `related_field` parameter to reference another field:

```python
class VarStruct(fields.Struct):
    length = fields.Int32Field(byteorder='big')
    data = fields.VariableBytesField(related_field='length')
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
uv sync

# Or install dev dependencies directly
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest --cov-report term --cov pystructs tests

# Run specific test file
pytest tests/fields/test_struct.py

# Run specific test
pytest tests/fields/test_struct.py::test_struct_can_have_recursive_struct
```

### Code Formatting

Black is enforced via GitHub Actions:

```bash
# Check formatting
black --check .

# Apply formatting
black .
```

### Test Writing Pattern

Tests use pytest fixtures and follow this structure:

```python
import pytest
from pystructs.fields import Struct, BytesField

@pytest.fixture
def my_struct():
    class CustomStruct(Struct):
        field = BytesField(size=4)

    struct = CustomStruct(b"1234")
    struct.initialize()
    return struct

def test_field_returns_expected_value(my_struct):
    assert my_struct.field == b"1234"
```

---

## Important Files Reference

| File | Role | When to Modify |
|------|------|----------------|
| `pystructs/fields/field.py` | Base class contract | Adding new field lifecycle methods |
| `pystructs/fields/struct.py` | Core parsing logic | Changing field linking or initialization |
| `pystructs/fields/bytes.py` | Byte extraction | Rarely - foundation class |
| `pystructs/utils.py` | Helper functions | Adding new utilities |
| `pystructs/__init__.py` | Public API exports | Adding new public types |
| `pystructs/fields/__init__.py` | Internal exports | Adding new field types |

---

## Guidelines for Making Changes

### Adding a New Field Type

1. Create file in `pystructs/fields/` (e.g., `newtype.py`)
2. Inherit from appropriate base (`BytesField` for byte-backed fields)
3. Implement `fetch()` method returning parsed value
4. Override `size` property if variable-length
5. Define `__all__` tuple with exported classes
6. Add import to `pystructs/fields/__init__.py`
7. Add to `__all__` tuple in both `fields/__init__.py` and `pystructs/__init__.py`
8. Create corresponding test file in `tests/fields/`
9. Run `black` for formatting

### Modifying Existing Behavior

1. Check existing tests to understand expected behavior
2. Write new tests for changed/added behavior FIRST
3. Make minimal changes to implementation
4. Ensure all tests pass: `pytest tests/`
5. Format code: `black .`

### Common Pitfalls to Avoid

1. **Forgetting `initialize()`** - Structs must call `initialize()` before accessing fields
2. **Circular imports** - Use `TYPE_CHECKING` guard for type hints:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from pystructs.fields import Struct
   ```
3. **Mutable class attributes** - `fields` dict is copied in `initialize()` via `deepcopy`
4. **Byteorder** - Integer fields default to 'little', explicitly set for network protocols

### Testing Checklist

- [ ] Test with different byte orders (big/little) for numeric fields
- [ ] Test edge cases (empty bytes, boundary values)
- [ ] Test nested structs if applicable
- [ ] Test variable-length fields with different sizes
- [ ] Verify error handling (TypeError, AttributeError)

---

## CI/CD Information

- **GitHub Actions**: Runs pytest with coverage on Python 3.9, 3.10, 3.11, 3.12
- **GitHub Actions**: Runs Black linting on push/PR
- **Codecov**: Coverage reporting
- **Read the Docs**: Documentation hosting
- **PyPI**: Deployment on tagged releases (main branch)
