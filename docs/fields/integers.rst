Integer Fields
==============

Integer fields parse and serialize fixed-size integer values.

Available Types
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 30

   * - Field
     - Size
     - Range
   * - ``Int8``
     - 1 byte
     - -128 to 127
   * - ``UInt8``
     - 1 byte
     - 0 to 255
   * - ``Int16``
     - 2 bytes
     - -32,768 to 32,767
   * - ``UInt16``
     - 2 bytes
     - 0 to 65,535
   * - ``Int32``
     - 4 bytes
     - -2^31 to 2^31-1
   * - ``UInt32``
     - 4 bytes
     - 0 to 2^32-1
   * - ``Int64``
     - 8 bytes
     - -2^63 to 2^63-1
   * - ``UInt64``
     - 8 bytes
     - 0 to 2^64-1

Basic Usage
-----------

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, Int32

   class Header(Struct):
       version = UInt8(default=1)
       flags = UInt16()
       offset = Int32()

   header = Header.parse(b"\x01\x0f\x00\xff\xff\xff\xff")
   print(header.version)  # 1
   print(header.flags)    # 15
   print(header.offset)   # -1

Endianness
----------

By default, integers use little-endian byte order. Override with ``Meta.endian``
or per-field ``endian`` parameter:

.. code-block:: python

   class NetworkHeader(Struct):
       class Meta:
           endian = "big"

       port = UInt16()
       sequence = UInt32()

   # Per-field override
   class MixedEndian(Struct):
       le_value = UInt32()  # Little-endian (default)
       be_value = UInt32(endian="big")  # Big-endian

API Reference
-------------

.. autoclass:: pystructs.fields.integers.IntField
   :members:

.. autoclass:: pystructs.fields.integers.Int8
.. autoclass:: pystructs.fields.integers.UInt8
.. autoclass:: pystructs.fields.integers.Int16
.. autoclass:: pystructs.fields.integers.UInt16
.. autoclass:: pystructs.fields.integers.Int32
.. autoclass:: pystructs.fields.integers.UInt32
.. autoclass:: pystructs.fields.integers.Int64
.. autoclass:: pystructs.fields.integers.UInt64
