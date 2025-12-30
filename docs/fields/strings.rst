String Fields
=============

String fields parse and serialize text data with various encoding options.

Available Types
---------------

- ``FixedString`` - Fixed-length string with padding
- ``String`` - Variable-length string (length from ``Ref``)
- ``NullTerminatedString`` - C-style null-terminated string

FixedString
-----------

Fixed-length string with optional padding:

.. code-block:: python

   from pystructs import Struct, FixedString

   class UserRecord(Struct):
       name = FixedString(length=20, encoding="utf-8", padding=b"\x00")
       email = FixedString(length=50)

   user = UserRecord(name="Alice", email="alice@example.com")
   raw = user.to_bytes()  # Name padded to 20 bytes

String (Variable-Length)
------------------------

Variable-length string with length from another field:

.. code-block:: python

   from pystructs import Struct, UInt8, String, Ref

   class Message(Struct):
       length = UInt8()
       text = String(length=Ref("length"))

   msg = Message.parse(b"\x05Hello")
   print(msg.text)  # "Hello"

NullTerminatedString
--------------------

C-style null-terminated string:

.. code-block:: python

   from pystructs import Struct, NullTerminatedString

   class CString(Struct):
       value = NullTerminatedString()

   s = CString.parse(b"Hello\x00World")
   print(s.value)  # "Hello"

API Reference
-------------

.. autoclass:: pystructs.fields.strings.FixedString
   :members:

.. autoclass:: pystructs.fields.strings.String
   :members:

.. autoclass:: pystructs.fields.strings.NullTerminatedString
   :members:
