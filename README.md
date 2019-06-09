# pystructs

`pystructs` is useful `c-like struct` package for human

## How to install

```bash
$ pip install pystructs
```

## Example codes

```python
from pystructs import fields, Struct

class MyStruct(Struct):
    byte = fields.BytesField(length=2)

MyStruct(b'\x00\x01').byte  # b'\x00\x01'
```