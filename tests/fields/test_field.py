import pytest

from pystructs import fields


def test_field_initialize_will_raise_error():
    with pytest.raises(NotImplementedError):
        class CustomStruct(fields.Struct):
            field = fields.Field(size=0)

        struct = CustomStruct(b'')
        struct.initialize()


def test_field_fetch_will_raise_error():
    with pytest.raises(NotImplementedError):
        field = fields.Field(size=2)
        field.fetch()


def test_field_import_struct_by_type_checking():
    from pystructs.fields import field

    if field.TYPE_CHECKING:
        assert getattr(field, 'Struct', None) is not None
