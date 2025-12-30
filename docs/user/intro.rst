Introduction
============

About
-----

**pystructs** is a Django-like declarative binary parsing library for Python.
It began with the desire to create a library that could handle binary data
comfortably, similar to C structures.

The key goals are:

- **Declarative** - Define struct layouts as class attributes, like Django models
- **Bidirectional** - Both parse binary data and serialize back to bytes
- **Composable** - Nest structs, use variable-length fields, and conditional logic
- **Zero dependencies** - Pure Python implementation with no runtime dependencies

Basic Concepts
--------------

Struct
~~~~~~

A ``Struct`` is a class that defines a binary data layout. Fields are declared
as class attributes:

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16

   class Header(Struct):
       magic = UInt8(default=0xFF)
       version = UInt8(default=1)
       length = UInt16()

Fields
~~~~~~

Fields define how to parse and serialize individual pieces of data:

- **Integer fields**: ``Int8``, ``UInt8``, ``Int16``, ``UInt16``, etc.
- **Bytes fields**: ``FixedBytes``, ``Bytes``
- **String fields**: ``FixedString``, ``String``, ``NullTerminatedString``
- **Composite fields**: ``Array``, ``EmbeddedStruct``, ``Conditional``, ``Switch``
- **Special fields**: ``Bool``, ``Padding``, ``Flags``, ``Enum``
- **Bit-level fields**: ``BitStruct``, ``Bit``, ``Bits``

Parsing and Serializing
~~~~~~~~~~~~~~~~~~~~~~~

Parse binary data with ``parse()``:

.. code-block:: python

   data = b"\xff\x01\x00\x10"
   header = Header.parse(data)
   print(header.magic)   # 255
   print(header.length)  # 16

Serialize to bytes with ``to_bytes()``:

.. code-block:: python

   header = Header(magic=0xAB, version=2, length=32)
   raw = header.to_bytes()

Ref System
~~~~~~~~~~

Use ``Ref`` to reference other fields for variable-length data:

.. code-block:: python

   from pystructs import Struct, UInt8, Bytes, Ref

   class Packet(Struct):
       length = UInt8()
       data = Bytes(size=Ref("length"))

   packet = Packet.parse(b"\x05Hello")
   print(packet.data)  # b'Hello'

Meta Class
~~~~~~~~~~

Configure struct options with an inner ``Meta`` class:

.. code-block:: python

   class NetworkPacket(Struct):
       class Meta:
           endian = "big"  # Network byte order

       port = UInt16()
       flags = UInt8()
