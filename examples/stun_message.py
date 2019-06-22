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


message = StunMessage(
    b'\x09\x00\x00\x00\x02'
    b'\x01\x00\x00\x00\x03\x12\x34\x56'
    b'\x02\x00\x00\x00\x03\x12\x34\x56')

message.initialize()

print(message.length)
print(message.attributes[0].length)
print(message.attributes[1].length)
