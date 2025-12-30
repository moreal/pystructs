Bytes Fields
============

Bytes fields parse and serialize raw binary data.

Available Types
---------------

- ``FixedBytes`` - Fixed-length bytes
- ``Bytes`` - Variable-length bytes (size from ``Ref`` or integer)

FixedBytes
----------

Fixed-length bytes field:

.. code-block:: python

   from pystructs import Struct, FixedBytes

   class Header(Struct):
       magic = FixedBytes(length=4)
       signature = FixedBytes(length=16)

   header = Header.parse(b"\x89PNG" + b"\x00" * 16)
   print(header.magic)  # b'\x89PNG'

Bytes (Variable-Length)
-----------------------

Variable-length bytes field with size from another field:

.. code-block:: python

   from pystructs import Struct, UInt16, Bytes, Ref

   class Packet(Struct):
       length = UInt16()
       data = Bytes(size=Ref("length"))

   packet = Packet.parse(b"\x05\x00Hello")
   print(packet.data)  # b'Hello'

With fixed size:

.. code-block:: python

   class Block(Struct):
       data = Bytes(size=1024)  # Always 1024 bytes

API Reference
-------------

.. autoclass:: pystructs.fields.bytes_fields.FixedBytes
   :members:

.. autoclass:: pystructs.fields.bytes_fields.Bytes
   :members:
