Validation
==========

pystructs provides a comprehensive validation system for ensuring data integrity.

Field Validators
----------------

Apply validators to individual fields:

.. code-block:: python

   from pystructs import Struct, UInt8, Range, OneOf

   class Packet(Struct):
       version = UInt8(validators=[Range(min_val=1, max_val=3)])
       packet_type = UInt8(validators=[OneOf([0x01, 0x02, 0xFF])])

   packet = Packet(version=5, packet_type=0x01)
   packet.validate()  # Raises ValidationErrors

Available Field Validators
--------------------------

- ``Range(min_val, max_val)`` - Value must be within range
- ``OneOf(choices)`` - Value must be one of the choices
- ``Regex(pattern)`` - String must match pattern
- ``BytePattern(pattern)`` - Bytes must match pattern

Struct Validators
-----------------

Apply validators at struct level in ``Meta.validators``:

.. code-block:: python

   from pystructs import Struct, UInt8, Bytes, Ref, Consistency, Custom, Len

   class Packet(Struct):
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

       version = UInt8()
       length = UInt8()
       data = Bytes(size=Ref("length"))

Available Struct Validators
---------------------------

- ``Consistency(field, equals=expr)`` - Field must equal expression
- ``Custom(func, message)`` - Custom validation function

Expressions
-----------

Use expressions in validators:

.. code-block:: python

   from pystructs import Len, Value, Const

   # Length of a field
   Len("data")

   # Value of a field
   Value("version")

   # Constant value
   Const(10)

Using validate()
----------------

Call ``validate()`` to check all rules:

.. code-block:: python

   try:
       packet.validate()
   except ValidationErrors as e:
       print(e)  # Lists all validation errors

Or use the ``validate`` parameter:

.. code-block:: python

   raw = packet.to_bytes(validate=True)
