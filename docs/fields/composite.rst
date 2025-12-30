Composite Fields
================

Composite fields combine multiple values or conditional logic.

Available Types
---------------

- ``Array`` - Repeated field values
- ``EmbeddedStruct`` - Nested struct
- ``Conditional`` - Optional field based on condition
- ``Switch`` - Tagged union (variant type)

Array
-----

Array of repeated field values:

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, Array, Ref

   class ScoreBoard(Struct):
       count = UInt8()
       scores = Array(UInt16(), count=Ref("count"))

   board = ScoreBoard.parse(b"\x03\x64\x00\xc8\x00\x2c\x01")
   print(board.scores)  # [100, 200, 300]

EmbeddedStruct
--------------

Nested struct within another struct:

.. code-block:: python

   from pystructs import Struct, UInt32, UInt8, EmbeddedStruct

   class Header(Struct):
       magic = UInt32(default=0xDEADBEEF)
       version = UInt8(default=1)

   class Packet(Struct):
       header = EmbeddedStruct(Header)
       payload_size = UInt16()

   packet = Packet.parse(b"\xef\xbe\xad\xde\x01\x00\x10")
   print(packet.header.magic)  # 3735928559

Conditional
-----------

Field that only exists when a condition is met:

.. code-block:: python

   from pystructs import Struct, UInt8, UInt32, Conditional, Ref

   class VersionedPacket(Struct):
       version = UInt8()
       # Only present in version 2+
       extended_header = Conditional(
           UInt32(),
           when=Ref("version") >= 2,
       )
       data = UInt8()

   # Version 1: no extended header
   v1 = VersionedPacket.parse(b"\x01\x42")
   print(v1.extended_header)  # None

   # Version 2: with extended header
   v2 = VersionedPacket.parse(b"\x02\x00\x00\x00\x01\x42")
   print(v2.extended_header)  # 1

Switch
------

Tagged union - select struct based on discriminator:

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, Switch, Ref

   class TextPayload(Struct):
       length = UInt8()

   class BinaryPayload(Struct):
       size = UInt16()

   class Message(Struct):
       msg_type = UInt8()
       payload = Switch(
           discriminator=Ref("msg_type"),
           cases={
               1: TextPayload,
               2: BinaryPayload,
           },
       )

   text_msg = Message.parse(b"\x01\x05")
   print(text_msg.payload.length)  # 5

API Reference
-------------

.. autoclass:: pystructs.fields.composite.Array
   :members:

.. autoclass:: pystructs.fields.composite.EmbeddedStruct
   :members:

.. autoclass:: pystructs.fields.composite.Conditional
   :members:

.. autoclass:: pystructs.fields.composite.Switch
   :members:
