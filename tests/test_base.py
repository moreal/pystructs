"""Tests for base field classes."""

import pytest

from pystructs.base import BaseField, FixedField


class TestBaseField:
    """Tests for BaseField abstract class."""

    def test_base_field_is_abstract(self):
        """BaseField cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseField()

    def test_fixed_field_get_size_returns_size_attribute(self):
        """FixedField.get_size returns the size class attribute."""

        class TestField(FixedField):
            size = 4

            def parse(self, buffer, instance):
                return buffer.read(self.size)

            def serialize(self, value, instance):
                return value

        field = TestField()
        assert field.get_size(None) == 4

    def test_field_set_name_sets_name(self):
        """__set_name__ properly sets the field name."""

        class TestField(FixedField):
            size = 2

            def parse(self, buffer, instance):
                return buffer.read(self.size)

            def serialize(self, value, instance):
                return value

        field = TestField()
        field.__set_name__(None, "my_field")
        assert field.name == "my_field"

    def test_field_default_values(self):
        """Field default values are properly set."""

        class TestField(FixedField):
            size = 1

            def parse(self, buffer, instance):
                return buffer.read(self.size)

            def serialize(self, value, instance):
                return value

        field = TestField(default=42, required=False)
        assert field.default == 42
        assert field.required is False
        assert field.validators == []

    def test_field_repr(self):
        """Field repr shows class name and field name."""

        class TestField(FixedField):
            size = 1

            def parse(self, buffer, instance):
                return buffer.read(self.size)

            def serialize(self, value, instance):
                return value

        field = TestField()
        field.__set_name__(None, "test")
        assert "TestField" in repr(field)
        assert "test" in repr(field)
