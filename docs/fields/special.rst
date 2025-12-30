Special Fields
==============

Special-purpose fields for common binary data patterns.

Available Types
---------------

- ``Bool`` - Boolean value (1 byte)
- ``Padding`` - Skip bytes (ignored during parsing)
- ``Flags`` - Bit flags with named flags
- ``Enum`` - Enum value mapping

Bool
----

Boolean field (1 byte, 0=False, non-zero=True):

.. code-block:: python

   from pystructs import Struct, Bool

   class Settings(Struct):
       enabled = Bool(default=True)
       verbose = Bool(default=False)

   s = Settings.parse(b"\x01\x00")
   print(s.enabled)  # True
   print(s.verbose)  # False

Padding
-------

Skip bytes during parsing, fill with value during serialization:

.. code-block:: python

   from pystructs import Struct, UInt8, Padding

   class AlignedData(Struct):
       value = UInt8()
       _pad = Padding(size=3)  # Align to 4 bytes
       next_value = UInt32()

Flags
-----

Bit flags with named flag values:

.. code-block:: python

   from pystructs import Struct, Flags

   class FileDescriptor(Struct):
       permissions = Flags(
           size=2,
           flags={
               "READ": 0x01,
               "WRITE": 0x02,
               "EXECUTE": 0x04,
           },
       )

   fd = FileDescriptor.parse(b"\x03\x00")
   print("READ" in fd.permissions)   # True
   print("WRITE" in fd.permissions)  # True
   print("EXECUTE" in fd.permissions)  # False

Enum
----

Map integer values to enum members:

.. code-block:: python

   from enum import IntEnum
   from pystructs import Struct, Enum

   class MessageType(IntEnum):
       REQUEST = 1
       RESPONSE = 2
       ERROR = 3

   class Message(Struct):
       msg_type = Enum(MessageType, size=1)

   msg = Message.parse(b"\x02")
   print(msg.msg_type)  # MessageType.RESPONSE
   print(msg.msg_type == MessageType.RESPONSE)  # True

API Reference
-------------

.. autoclass:: pystructs.fields.special.Bool
   :members:

.. autoclass:: pystructs.fields.special.Padding
   :members:

.. autoclass:: pystructs.fields.special.Flags
   :members:

.. autoclass:: pystructs.fields.special.Enum
   :members:
