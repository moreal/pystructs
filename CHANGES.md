# pystructs changelog

## Version 0.4.0

Released on December 2024.

### Breaking Changes

- Complete API redesign with Django-like declarative syntax
- Removed: `initialize()`, `fetch()`, `BytesField`, `VariableBytesField`, `MultipleField`
- New: `Struct.parse()`, `to_bytes()`, `Ref`, `SyncRule`, validators
- Field access now uses descriptor protocol (no more `initialize()` required)

### New Features

- **Bidirectional parsing** - Both `parse()` and `to_bytes()` methods
- **Ref system** - Cross-field references with `Ref("field_name")`
- **SyncRule** - Automatic field synchronization (e.g., length fields)
- **Validation system** - `Range`, `OneOf`, `Consistency`, `Custom` validators
- **BitStruct** - Bit-level parsing with `Bit` and `Bits` fields
- **Conditional** - Optional fields based on runtime conditions
- **Switch** - Tagged unions for variant types
- **Flags** - Bit flags field with named flags
- **Enum** - Enum field for type-safe enum handling
- **Float32/Float64** - Floating-point number fields
- **Expression system** - `Len`, `Value`, `Const`, `Checksum` for validation

### New Field Types

- Integer: `Int8`, `UInt8`, `Int16`, `UInt16`, `Int32`, `UInt32`, `Int64`, `UInt64`
- Float: `Float32`, `Float64`
- Bytes: `FixedBytes`, `Bytes`
- String: `FixedString`, `String`, `NullTerminatedString`
- Composite: `Array`, `EmbeddedStruct`, `Conditional`, `Switch`
- Special: `Bool`, `Padding`, `Flags`, `Enum`
- Bit-level: `BitStruct`, `Bit`, `Bits`, `EmbeddedBitStruct`

---

## Version 0.3.0

Released on August 27, 2019.

- `Struct` inheritance became available.
- `Int8Field`, `Int16Field` was added.
- `Struct` became to let self initialize automatically.

## Version 0.2.1

Just chore to be better for docs. Released on June 26, 2019.

## Version 0.2.0

Released on June 22, 2019.

- `VariableBytesField` is added.
- `StringField` is added.
- `MultipleField` is added.
- `IntField`, `Int32Field`, `Int64Field` is added.

## Version 0.1.1

Just chore like README. Released on June 9, 2019.

## Version 0.1.0

Initial release. Released on June 9, 2019.
