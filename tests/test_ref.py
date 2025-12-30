"""Tests for the Ref system."""

from pystructs import Ref, Struct, UInt8, UInt16
from pystructs.ref import RefComparison, RefLogical


class TestRef:
    """Tests for Ref class."""

    def test_ref_resolve_simple_field(self):
        """Ref resolves a simple field reference."""

        class Simple(Struct):
            length = UInt8()
            value = UInt16()

        s = Simple(length=10, value=20)
        ref = Ref("length")
        assert ref.resolve(s) == 10

    def test_ref_resolve_dot_notation(self):
        """Ref resolves nested field with dot notation."""

        class Inner(Struct):
            size = UInt16()

        class Outer(Struct):
            header = UInt8()

        # We need nested structs for this, which comes in Phase 5
        # For now, test that the mechanism works with simple getattr
        class MockInstance:
            class header:
                size = 42

            _parent = None
            _root = None

        MockInstance._root = MockInstance

        ref = Ref("header.size")
        assert ref.resolve(MockInstance) == 42

    def test_ref_repr(self):
        """Ref repr shows the path."""
        ref = Ref("field_name")
        assert "field_name" in repr(ref)


class TestRefComparison:
    """Tests for RefComparison."""

    def test_ref_eq_comparison(self):
        """Ref == value creates RefComparison."""

        class Simple(Struct):
            version = UInt8()

        s = Simple(version=2)
        comparison = Ref("version") == 2
        assert isinstance(comparison, RefComparison)
        assert comparison.evaluate(s) is True

        comparison2 = Ref("version") == 3
        assert comparison2.evaluate(s) is False

    def test_ref_ne_comparison(self):
        """Ref != value creates RefComparison."""

        class Simple(Struct):
            version = UInt8()

        s = Simple(version=2)
        comparison = Ref("version") != 2
        assert comparison.evaluate(s) is False

        comparison2 = Ref("version") != 3
        assert comparison2.evaluate(s) is True

    def test_ref_lt_comparison(self):
        """Ref < value creates RefComparison."""

        class Simple(Struct):
            version = UInt8()

        s = Simple(version=2)
        assert (Ref("version") < 3).evaluate(s) is True
        assert (Ref("version") < 2).evaluate(s) is False
        assert (Ref("version") < 1).evaluate(s) is False

    def test_ref_le_comparison(self):
        """Ref <= value creates RefComparison."""

        class Simple(Struct):
            version = UInt8()

        s = Simple(version=2)
        assert (Ref("version") <= 3).evaluate(s) is True
        assert (Ref("version") <= 2).evaluate(s) is True
        assert (Ref("version") <= 1).evaluate(s) is False

    def test_ref_gt_comparison(self):
        """Ref > value creates RefComparison."""

        class Simple(Struct):
            version = UInt8()

        s = Simple(version=2)
        assert (Ref("version") > 1).evaluate(s) is True
        assert (Ref("version") > 2).evaluate(s) is False
        assert (Ref("version") > 3).evaluate(s) is False

    def test_ref_ge_comparison(self):
        """Ref >= value creates RefComparison."""

        class Simple(Struct):
            version = UInt8()

        s = Simple(version=2)
        assert (Ref("version") >= 1).evaluate(s) is True
        assert (Ref("version") >= 2).evaluate(s) is True
        assert (Ref("version") >= 3).evaluate(s) is False


class TestRefLogical:
    """Tests for RefLogical (combining comparisons)."""

    def test_and_combination(self):
        """Two comparisons can be combined with &."""

        class Simple(Struct):
            version = UInt8()
            flags = UInt8()

        s = Simple(version=2, flags=1)

        combined = (Ref("version") >= 2) & (Ref("flags") == 1)
        assert isinstance(combined, RefLogical)
        assert combined.evaluate(s) is True

        combined2 = (Ref("version") >= 3) & (Ref("flags") == 1)
        assert combined2.evaluate(s) is False

    def test_or_combination(self):
        """Two comparisons can be combined with |."""

        class Simple(Struct):
            version = UInt8()
            flags = UInt8()

        s = Simple(version=2, flags=1)

        combined = (Ref("version") >= 3) | (Ref("flags") == 1)
        assert combined.evaluate(s) is True

        combined2 = (Ref("version") >= 3) | (Ref("flags") == 0)
        assert combined2.evaluate(s) is False

    def test_complex_logical_expression(self):
        """Complex logical expressions work correctly."""

        class Simple(Struct):
            a = UInt8()
            b = UInt8()
            c = UInt8()

        s = Simple(a=1, b=2, c=3)

        # (a == 1 and b == 2) or c == 0
        expr = ((Ref("a") == 1) & (Ref("b") == 2)) | (Ref("c") == 0)
        assert expr.evaluate(s) is True

        # (a == 0 and b == 0) or c == 0
        expr2 = ((Ref("a") == 0) & (Ref("b") == 0)) | (Ref("c") == 0)
        assert expr2.evaluate(s) is False
