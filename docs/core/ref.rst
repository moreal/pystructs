Ref System
==========

The ``Ref`` class enables cross-field references for variable-length fields
and conditional logic.

Basic Usage
-----------

Reference another field's value:

.. code-block:: python

   from pystructs import Struct, UInt8, Bytes, Ref

   class Packet(Struct):
       length = UInt8()
       data = Bytes(size=Ref("length"))

   packet = Packet.parse(b"\x05Hello")
   print(packet.data)  # b'Hello'

Path Syntax
-----------

Ref supports various path formats:

.. code-block:: python

   # Same level field
   Ref("field_name")

   # Nested field (dot notation)
   Ref("header.length")

   # Parent struct field
   Ref("../length")

   # Absolute path from root
   Ref("/header/length")

Comparisons
-----------

Use comparisons for conditional fields:

.. code-block:: python

   from pystructs import Struct, UInt8, UInt32, Conditional, Ref

   class Message(Struct):
       version = UInt8()

       # Equal
       v1_data = Conditional(UInt32(), when=Ref("version") == 1)

       # Not equal
       new_data = Conditional(UInt32(), when=Ref("version") != 1)

       # Greater/less than
       extended = Conditional(UInt32(), when=Ref("version") >= 2)

Logical Operators
-----------------

Combine comparisons with ``&`` (and) and ``|`` (or):

.. code-block:: python

   class Packet(Struct):
       version = UInt8()
       flags = UInt8()

       optional = Conditional(
           UInt32(),
           when=(Ref("version") >= 2) & (Ref("flags") != 0),
       )
