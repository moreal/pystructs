.. pystructs documentation master file

Welcome to pystructs' documentation!
=====================================

**pystructs** is a Django-like declarative binary parsing library for Python.
Define binary data structures as classes and parse/serialize them with ease.

Quick Example
-------------

.. code-block:: python

   from pystructs import Struct, UInt8, UInt16, UInt32, Bytes, Ref, SyncRule

   class Packet(Struct):
       class Meta:
           endian = "big"
           sync_rules = [
               SyncRule("length", from_field="payload", compute=len),
           ]

       magic = UInt32(default=0xDEADBEEF)
       version = UInt8(default=1)
       length = UInt16()
       payload = Bytes(size=Ref("length"))

   # Parse from bytes
   data = b"\xde\xad\xbe\xef\x01\x00\x05Hello"
   packet = Packet.parse(data)
   print(packet.magic)    # 3735928559
   print(packet.payload)  # b'Hello'

   # Create and serialize
   new_packet = Packet(payload=b"World")
   new_packet.sync()
   print(new_packet.to_bytes())

Features
--------

- **Declarative syntax** - Define structs like Django models
- **Bidirectional** - Parse binary data and serialize back to bytes
- **Rich field types** - Integers, floats, bytes, strings, arrays, and more
- **Bit-level parsing** - `BitStruct` for parsing individual bits
- **Conditional fields** - Fields that exist based on runtime conditions
- **Validation system** - Built-in and custom validators
- **Zero runtime dependencies** - Pure Python implementation

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   user/intro
   user/quickstart

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   core/struct
   core/ref
   core/sync
   core/validation

.. toctree::
   :maxdepth: 2
   :caption: Field Types

   fields/integers
   fields/floats
   fields/bytes
   fields/strings
   fields/composite
   fields/special
   fields/bitfields

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/base
   api/struct
   api/ref
   api/sync
   api/validate
   api/expressions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
