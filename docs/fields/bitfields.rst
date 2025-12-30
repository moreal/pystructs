Bit Fields
==========

Bit-level parsing for protocols that pack data at the bit level.

Available Types
---------------

- ``BitStruct`` - Container for bit-level fields
- ``Bit`` - Single bit (boolean)
- ``Bits`` - Multiple bits (integer)
- ``EmbeddedBitStruct`` - Embed BitStruct in a Struct

BitStruct
---------

Define a bit-level structure:

.. code-block:: python

   from pystructs import BitStruct, Bit, Bits

   class TCPFlags(BitStruct):
       class Meta:
           size = 1  # 1 byte = 8 bits

       fin = Bit()
       syn = Bit()
       rst = Bit()
       psh = Bit()
       ack = Bit()
       urg = Bit()
       reserved = Bits(2)

   flags = TCPFlags.parse(b"\x12")
   print(flags.syn)  # True
   print(flags.ack)  # True

Bit
---

Single bit field (boolean value):

.. code-block:: python

   class Flags(BitStruct):
       class Meta:
           size = 1

       enabled = Bit()
       active = Bit()
       ready = Bit()
       # ...

Bits
----

Multiple bits field (integer value):

.. code-block:: python

   class ControlByte(BitStruct):
       class Meta:
           size = 1

       mode = Bits(3)      # 3 bits: 0-7
       priority = Bits(2)  # 2 bits: 0-3
       reserved = Bits(3)

   ctrl = ControlByte.parse(b"\x4a")
   print(ctrl.mode)      # 2
   print(ctrl.priority)  # 1

EmbeddedBitStruct
-----------------

Embed a BitStruct within a regular Struct:

.. code-block:: python

   from pystructs import Struct, UInt16, EmbeddedBitStruct

   class TCPHeader(Struct):
       class Meta:
           endian = "big"

       src_port = UInt16()
       dst_port = UInt16()
       flags = EmbeddedBitStruct(TCPFlags)

   header = TCPHeader.parse(b"\x00\x50\x1f\x90\x12")
   print(header.src_port)   # 80
   print(header.flags.syn)  # True

Multi-Byte BitStruct
--------------------

For bit fields spanning multiple bytes:

.. code-block:: python

   class StatusRegister(BitStruct):
       class Meta:
           size = 2  # 16 bits

       error_code = Bits(4)
       warning_level = Bits(4)
       state = Bits(4)
       version = Bits(4)

API Reference
-------------

.. autoclass:: pystructs.fields.bitfields.BitStruct
   :members:

.. autoclass:: pystructs.fields.bitfields.Bit
   :members:

.. autoclass:: pystructs.fields.bitfields.Bits
   :members:

.. autoclass:: pystructs.fields.bitfields.EmbeddedBitStruct
   :members:
