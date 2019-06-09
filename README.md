# pystructs

[![Build Status](https://travis-ci.com/moreal/pystructs.svg?branch=master)](https://travis-ci.com/moreal/pystructs)
[![codecov](https://codecov.io/gh/moreal/pystructs/branch/master/graph/badge.svg)](https://codecov.io/gh/moreal/pystructs)

`pystructs` is useful `c-like struct` package for human

## How to install

```bash
$ pip install pystructs
```

## Example codes

```python
from pystructs import fields

class MyStruct(fields.Struct):
    byte = fields.BytesField(size=2)

MyStruct(b'\x00\x01').byte  # b'\x00\x01'
```