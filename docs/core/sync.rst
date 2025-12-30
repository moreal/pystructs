Sync System
===========

The sync system automatically updates field values based on other fields,
typically used for length/count fields.

SyncRule
--------

Define sync rules in ``Meta.sync_rules``:

.. code-block:: python

   from pystructs import Struct, UInt8, Bytes, Ref, SyncRule

   class Packet(Struct):
       class Meta:
           sync_rules = [
               SyncRule("length", from_field="data", compute=len),
           ]

       length = UInt8()
       data = Bytes(size=Ref("length"))

   # Create packet
   packet = Packet(data=b"Hello World")
   packet.sync()  # length = 11

   print(packet.length)  # 11

Using sync()
------------

Call ``sync()`` before serialization:

.. code-block:: python

   packet = Packet(data=b"Test")
   packet.sync()
   raw = packet.to_bytes()

Or use the ``sync`` parameter:

.. code-block:: python

   raw = packet.to_bytes(sync=True)

Custom Compute Functions
------------------------

Use any callable for computation:

.. code-block:: python

   class Packet(Struct):
       class Meta:
           sync_rules = [
               # Length of data
               SyncRule("length", from_field="data", compute=len),
               # Checksum
               SyncRule("checksum", from_field="data", compute=lambda d: sum(d) & 0xFF),
           ]

       length = UInt8()
       checksum = UInt8()
       data = Bytes(size=Ref("length"))

Multiple Source Fields
----------------------

Compute from multiple fields with ``from_fields``:

.. code-block:: python

   class Packet(Struct):
       class Meta:
           sync_rules = [
               SyncRule(
                   "total",
                   from_fields=["header", "data"],
                   compute=lambda h, d: len(h.to_bytes()) + len(d),
               ),
           ]

       total = UInt16()
       header = EmbeddedStruct(Header)
       data = Bytes(size=10)
