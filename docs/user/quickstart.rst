Quick Start
===========

Installation
------------

Install pystructs using pip:

.. code-block:: bash

   pip install pystructs

Basic Usage
-----------

Define a Struct
~~~~~~~~~~~~~~~

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, UInt32

   class Header(Struct):
       magic = UInt32(default=0xDEADBEEF)
       version = UInt8(default=1)
       flags = UInt8()
       length = UInt16()

Parse Binary Data
~~~~~~~~~~~~~~~~~

.. code-block:: python

   data = b"\xef\xbe\xad\xde\x01\x0f\x00\x10"
   header = Header.parse(data)

   print(header.magic)    # 3735928559
   print(header.version)  # 1
   print(header.flags)    # 15
   print(header.length)   # 16

Create and Serialize
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   header = Header(flags=0x0F, length=100)
   raw = header.to_bytes()
   print(raw.hex())  # efbeadde010f6400

Variable-Length Fields
----------------------

Use ``Ref`` to reference other fields:

.. code-block:: python

   from pystructs import Struct, UInt8, Bytes, Ref, SyncRule

   class Packet(Struct):
       class Meta:
           sync_rules = [
               SyncRule("length", from_field="payload", compute=len),
           ]

       length = UInt8()
       payload = Bytes(size=Ref("length"))

   # Parse
   packet = Packet.parse(b"\x05Hello")
   print(packet.payload)  # b'Hello'

   # Create and serialize
   packet = Packet(payload=b"World")
   packet.sync()  # Auto-calculate length
   print(packet.to_bytes())  # b'\x05World'

Arrays
------

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, Array, Ref

   class ScoreBoard(Struct):
       count = UInt8()
       scores = Array(UInt16(), count=Ref("count"))

   data = b"\x03\x64\x00\xc8\x00\x2c\x01"
   board = ScoreBoard.parse(data)
   print(board.scores)  # [100, 200, 300]

Endianness
----------

Set byte order with ``Meta.endian``:

.. code-block:: python

   class NetworkPacket(Struct):
       class Meta:
           endian = "big"  # Network byte order

       port = UInt16()
       flags = UInt8()

   packet = NetworkPacket.parse(b"\x00\x50\x01")
   print(packet.port)  # 80

Next Steps
----------

- Learn about :doc:`../core/struct` for advanced struct features
- Explore :doc:`../fields/composite` for nested structures
- See :doc:`../fields/bitfields` for bit-level parsing
