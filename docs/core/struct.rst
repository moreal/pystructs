Struct
======

The ``Struct`` class is the foundation of pystructs. It provides declarative
binary structure definition with automatic parsing and serialization.

Defining a Struct
-----------------

Define fields as class attributes:

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, UInt32

   class Header(Struct):
       magic = UInt32(default=0xDEADBEEF)
       version = UInt8(default=1)
       flags = UInt8()
       length = UInt16()

Meta Class
----------

Configure struct behavior with an inner ``Meta`` class:

.. code-block:: python

   from pystructs import Struct, UInt16, SyncRule

   class Packet(Struct):
       class Meta:
           endian = "big"           # Byte order
           trailing_data = "ignore" # or "error", "warn"
           sync_rules = [
               SyncRule("length", from_field="data", compute=len),
           ]
           validators = [
               # Struct-level validators
           ]

       length = UInt16()
       data = Bytes(size=Ref("length"))

Parsing
-------

Parse binary data with ``parse()``:

.. code-block:: python

   data = b"\xef\xbe\xad\xde\x01\x0f\x00\x10"
   header = Header.parse(data)

   # Access fields directly
   print(header.magic)    # 3735928559
   print(header.version)  # 1

Handle trailing data:

.. code-block:: python

   # Ignore trailing data
   header = Header.parse(data_with_extra, allow_trailing=True)

   # Or configure in Meta
   class Packet(Struct):
       class Meta:
           trailing_data = "ignore"  # "error" (default), "warn", "ignore"

Serialization
-------------

Serialize to bytes with ``to_bytes()``:

.. code-block:: python

   header = Header(flags=0x0F, length=100)
   raw = header.to_bytes()

With sync and validation:

.. code-block:: python

   packet = Packet(data=b"Hello")
   raw = packet.to_bytes(sync=True, validate=True)

Struct Inheritance
------------------

Structs support inheritance:

.. code-block:: python

   class BaseHeader(Struct):
       magic = UInt32(default=0xDEADBEEF)
       version = UInt8(default=1)

   class ExtendedHeader(BaseHeader):
       flags = UInt8()
       length = UInt16()

Converting to Dict
------------------

Convert struct to dictionary:

.. code-block:: python

   header = Header.parse(data)
   d = header.to_dict()
   # {'magic': 3735928559, 'version': 1, 'flags': 15, 'length': 16}
