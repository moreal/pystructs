# pystructs

[![Documentation Status](https://readthedocs.org/projects/pystructs/badge/?version=0.2.1)](https://pystructs.readthedocs.io/en/latest/?badge=0.2.1)
[![Build Status](https://travis-ci.com/moreal/pystructs.svg?branch=master)](https://travis-ci.com/moreal/pystructs)
[![codecov](https://codecov.io/gh/moreal/pystructs/branch/master/graph/badge.svg)](https://codecov.io/gh/moreal/pystructs)
[![slack](https://img.shields.io/badge/slack-pystructs-yellow.svg?logo=slack)](https://pystructs-slack-application.herokuapp.com/)

`pystructs` is useful `c-like struct` package for human

## How to install

```bash
$ pip install pystructs
```

## Example codes

```python
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

print(message.length)  # 2
print(message.attributes[0].length)  # 3
print(message.attributes[1].length)  # 3
```