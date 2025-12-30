Float Fields
============

Float fields parse and serialize IEEE 754 floating-point values.

Available Types
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 30

   * - Field
     - Size
     - Description
   * - ``Float32``
     - 4 bytes
     - Single precision (32-bit)
   * - ``Float64``
     - 8 bytes
     - Double precision (64-bit)

Basic Usage
-----------

.. code-block:: python

   from pystructs import Struct, Float32, Float64

   class Measurement(Struct):
       temperature = Float32()
       pressure = Float64()

   data = b"\x00\x00\xc8\x42\x00\x00\x00\x00\x00\x88\xc3\x40"
   m = Measurement.parse(data)
   print(m.temperature)  # 100.0
   print(m.pressure)     # 10000.0

API Reference
-------------

.. autoclass:: pystructs.fields.floats.Float32
.. autoclass:: pystructs.fields.floats.Float64
