.. pystructs documentation master file, created by
   sphinx-quickstart on Mon Jun 24 09:49:05 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pystructs' documentation!
=====================================

.. code-block:: python

   from typing import List
   from pystructs import fields

   class Attribute(fields.Struct):
       type = fields.BytesField(size=1)
       length = fields.Int32Field(byteorder='big')
       value = fields.VariableBytesField(related_field='length')


   class StunMessage(fields.Struct):
       type = fields.BytesField(size=1)
       length = fields.Int32Field(byteorder='big')
       attributes: List[Attribute] = fields.MultipleField(count='length', field=Attribute())

   message = StunMessage(<bytes>)
   message.initialize()

   # Just use!


.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   user/intro

.. toctree::
   :maxdepth: 2
   :caption: Fields

   fields/field
   fields/struct
