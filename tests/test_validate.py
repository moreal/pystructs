"""Tests for the validation system."""

import pytest

from pystructs import (
    BytePattern,
    Bytes,
    Checksum,
    Consistency,
    Custom,
    FixedBytes,
    FixedString,
    InconsistencyError,
    Len,
    OneOf,
    Range,
    Ref,
    Regex,
    Struct,
    UInt8,
    UInt32,
    ValidationErrors,
)


class TestRange:
    """Tests for Range field validator."""

    def test_value_in_range(self):
        """Value within range passes."""

        class S(Struct):
            value = UInt8(validators=[Range(1, 10)])

        s = S(value=5)
        s.validate()  # Should not raise

    def test_value_below_min(self):
        """Value below min fails."""

        class S(Struct):
            value = UInt8(validators=[Range(min_val=5)])

        s = S(value=3)
        with pytest.raises(ValidationErrors):
            s.validate()

    def test_value_above_max(self):
        """Value above max fails."""

        class S(Struct):
            value = UInt8(validators=[Range(max_val=10)])

        s = S(value=15)
        with pytest.raises(ValidationErrors):
            s.validate()

    def test_value_at_boundary(self):
        """Values at boundary pass (inclusive)."""

        class S(Struct):
            value = UInt8(validators=[Range(1, 10)])

        s1 = S(value=1)
        s1.validate()  # Min boundary

        s2 = S(value=10)
        s2.validate()  # Max boundary


class TestOneOf:
    """Tests for OneOf field validator."""

    def test_value_in_choices(self):
        """Value in choices passes."""

        class S(Struct):
            msg_type = UInt8(validators=[OneOf([1, 2, 3])])

        s = S(msg_type=2)
        s.validate()

    def test_value_not_in_choices(self):
        """Value not in choices fails."""

        class S(Struct):
            msg_type = UInt8(validators=[OneOf([1, 2, 3])])

        s = S(msg_type=5)
        with pytest.raises(ValidationErrors):
            s.validate()


class TestRegex:
    """Tests for Regex field validator."""

    def test_pattern_matches(self):
        """Pattern match passes."""

        class S(Struct):
            name = FixedString(10, validators=[Regex(r"^[a-zA-Z]+$")])

        s = S(name="Hello")
        s.validate()

    def test_pattern_not_matches(self):
        """Pattern mismatch fails."""

        class S(Struct):
            name = FixedString(10, validators=[Regex(r"^[a-zA-Z]+$")])

        s = S(name="Hello123")
        with pytest.raises(ValidationErrors):
            s.validate()


class TestBytePattern:
    """Tests for BytePattern field validator."""

    def test_pattern_matches(self):
        """Bytes start with pattern passes."""

        class S(Struct):
            data = FixedBytes(8, validators=[BytePattern(b"MAGIC")])

        s = S(data=b"MAGIC123")
        s.validate()

    def test_pattern_not_matches(self):
        """Bytes not starting with pattern fails."""

        class S(Struct):
            data = FixedBytes(8, validators=[BytePattern(b"MAGIC")])

        s = S(data=b"BADDATA!")
        with pytest.raises(ValidationErrors):
            s.validate()


class TestConsistency:
    """Tests for Consistency struct validator."""

    def test_equals_consistent(self):
        """Field equals expected value passes."""

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("length", equals=Len("data")),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=5, data=b"Hello")
        s.validate()

    def test_equals_inconsistent(self):
        """Field not equal to expected value fails."""

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("length", equals=Len("data")),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        # Create with inconsistent values (dumb creation allowed)
        s = S.__new__(S)
        s._data = {"length": 10, "data": b"Hello"}  # 10 != 5
        s._meta = S._meta
        s._parent = None
        s._root = s

        with pytest.raises(ValidationErrors) as exc_info:
            s.validate()

        # Check that InconsistencyError is in the errors
        assert any(isinstance(e, InconsistencyError) for e in exc_info.value.errors)

    def test_checksum_consistent(self):
        """Checksum validation passes."""
        import binascii

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("checksum", equals=Checksum("data", "crc32")),
                ]

            data = Bytes(size=5)
            checksum = UInt32()

        data = b"Hello"
        expected_crc = binascii.crc32(data) & 0xFFFFFFFF

        s = S(data=data, checksum=expected_crc)
        s.validate()

    def test_greater_than(self):
        """greater_than validation."""
        from pystructs.expressions import Const

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("value", greater_than=Const(10)),
                ]

            value = UInt8()

        s1 = S(value=15)
        s1.validate()  # 15 > 10, passes

        s2 = S(value=5)
        with pytest.raises(ValidationErrors):
            s2.validate()  # 5 > 10, fails

    def test_less_than(self):
        """less_than validation."""
        from pystructs.expressions import Const

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("value", less_than=Const(100)),
                ]

            value = UInt8()

        s1 = S(value=50)
        s1.validate()  # 50 < 100, passes

        s2 = S(value=150)
        with pytest.raises(ValidationErrors):
            s2.validate()  # 150 < 100, fails


class TestCustom:
    """Tests for Custom struct validator."""

    def test_custom_passes(self):
        """Custom validation passes."""

        class S(Struct):
            class Meta:
                validators = [
                    Custom(lambda self: self.version in (1, 2, 3), "Invalid version"),
                ]

            version = UInt8()

        s = S(version=2)
        s.validate()

    def test_custom_fails(self):
        """Custom validation fails."""

        class S(Struct):
            class Meta:
                validators = [
                    Custom(lambda self: self.version in (1, 2, 3), "Invalid version"),
                ]

            version = UInt8()

        s = S(version=5)
        with pytest.raises(ValidationErrors) as exc_info:
            s.validate()

        assert "Invalid version" in str(exc_info.value)


class TestValidateMethodChaining:
    """Tests for validate() method chaining."""

    def test_validate_returns_self(self):
        """validate() returns self for chaining."""

        class S(Struct):
            value = UInt8()

        s = S(value=5)
        result = s.validate()
        assert result is s


class TestToBytesWithValidate:
    """Tests for to_bytes(validate=True)."""

    def test_to_bytes_with_validate_passes(self):
        """to_bytes with validate=True works when valid."""

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("length", equals=Len("data")),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=5, data=b"Hello")
        raw = s.to_bytes(validate=True)
        assert raw == bytes([5]) + b"Hello"

    def test_to_bytes_with_validate_fails(self):
        """to_bytes with validate=True fails when invalid."""

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("length", equals=Len("data")),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S.__new__(S)
        s._data = {"length": 99, "data": b"Hello"}
        s._meta = S._meta
        s._parent = None
        s._root = s

        with pytest.raises(ValidationErrors):
            s.to_bytes(validate=True)


class TestMultipleValidators:
    """Tests for multiple validators."""

    def test_multiple_field_validators(self):
        """Multiple validators on a field."""

        class S(Struct):
            value = UInt8(validators=[Range(1, 100), OneOf([10, 20, 30, 40, 50])])

        s1 = S(value=20)
        s1.validate()  # Both pass

        s2 = S(value=15)  # In range but not in OneOf
        with pytest.raises(ValidationErrors):
            s2.validate()

    def test_field_and_struct_validators(self):
        """Both field-level and struct-level validators."""

        class S(Struct):
            class Meta:
                validators = [
                    Consistency("length", equals=Len("data")),
                ]

            length = UInt8(validators=[Range(1, 255)])
            data = Bytes(size=Ref("length"))

        s = S(length=5, data=b"Hello")
        s.validate()
