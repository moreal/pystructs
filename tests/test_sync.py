"""Tests for the sync system."""

from pystructs import Bytes, Ref, Struct, SyncRule, UInt8, UInt16, UInt32


class TestSyncRule:
    """Tests for SyncRule class."""

    def test_sync_from_single_field(self):
        """Sync target from single source field."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("length", from_field="data", compute=len),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=0, data=b"Hello")
        s.sync()
        assert s.length == 5

    def test_sync_from_multiple_fields(self):
        """Sync target from multiple source fields."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule(
                        "total",
                        from_fields=["a", "b"],
                        compute=lambda a, b: a + b,
                    ),
                ]

            a = UInt8()
            b = UInt8()
            total = UInt16()

        s = S(a=10, b=20, total=0)
        s.sync()
        assert s.total == 30

    def test_sync_from_instance(self):
        """Sync target using instance reference."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("checksum", compute=lambda self: sum(self.data)),
                ]

            data = Bytes(size=4)
            checksum = UInt32()

        s = S(data=b"\x01\x02\x03\x04", checksum=0)
        s.sync()
        assert s.checksum == 10  # 1 + 2 + 3 + 4

    def test_sync_method_chaining(self):
        """sync() returns self for method chaining."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("length", from_field="data", compute=len),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=0, data=b"Test")
        result = s.sync()
        assert result is s
        assert s.length == 4

    def test_sync_specific_fields(self):
        """Sync only specific fields."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("len1", from_field="data1", compute=len),
                    SyncRule("len2", from_field="data2", compute=len),
                ]

            len1 = UInt8()
            data1 = Bytes(size=Ref("len1"))
            len2 = UInt8()
            data2 = Bytes(size=Ref("len2"))

        s = S(len1=0, data1=b"AAA", len2=0, data2=b"BBBBB")
        s.sync(fields=["len1"])  # Only sync len1
        assert s.len1 == 3
        assert s.len2 == 0  # Not synced


class TestSyncWithToBytes:
    """Tests for sync with to_bytes()."""

    def test_to_bytes_with_sync(self):
        """to_bytes(sync=True) runs sync before serializing."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("length", from_field="data", compute=len),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=0, data=b"Test")
        raw = s.to_bytes(sync=True)
        assert raw[0] == 4  # length updated to 4
        assert raw[1:] == b"Test"

    def test_to_bytes_without_sync(self):
        """to_bytes() without sync uses existing values."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("length", from_field="data", compute=len),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        s = S(length=99, data=b"Test")  # Inconsistent length
        raw = s.to_bytes()  # No sync
        assert raw[0] == 99  # Original inconsistent value


class TestSyncComplexExamples:
    """Tests for complex sync scenarios."""

    def test_sync_payload_size(self):
        """Sync payload size like in NEXT_PLAN.md example."""

        class Packet(Struct):
            class Meta:
                endian = "big"
                sync_rules = [
                    SyncRule("payload_size", from_field="payload", compute=len),
                ]

            magic = UInt32(default=0xDEADBEEF)
            version = UInt8(default=1)
            payload_size = UInt16()
            payload = Bytes(size=Ref("payload_size"))

        # Create packet with payload
        packet = Packet(payload=b"Hello, World!")
        packet.sync()

        assert packet.payload_size == 13  # len("Hello, World!")

        # Serialize and verify
        raw = packet.to_bytes()
        assert raw[:4] == b"\xde\xad\xbe\xef"  # magic (big-endian)
        assert raw[4] == 1  # version
        assert raw[5:7] == b"\x00\x0d"  # payload_size = 13 (big-endian)
        assert raw[7:] == b"Hello, World!"

    def test_sync_total_size(self):
        """Sync total size from multiple fields."""

        class Message(Struct):
            class Meta:
                sync_rules = [
                    SyncRule(
                        "total_size",
                        from_fields=["header", "payload"],
                        compute=lambda h, p: len(h) + len(p),
                    ),
                ]

            total_size = UInt16()
            header = Bytes(size=4)
            payload = Bytes(size=8)

        msg = Message(
            total_size=0,
            header=b"HEAD",
            payload=b"PAYLOADX",
        )
        msg.sync()
        assert msg.total_size == 12


class TestSyncRoundTrip:
    """Tests for sync in parse/modify/serialize workflow."""

    def test_modify_and_resync(self):
        """Parse, modify, sync, and serialize."""

        class S(Struct):
            class Meta:
                sync_rules = [
                    SyncRule("length", from_field="data", compute=len),
                ]

            length = UInt8()
            data = Bytes(size=Ref("length"))

        # Parse original data
        original = bytes([5, 0x48, 0x65, 0x6C, 0x6C, 0x6F])  # length=5, "Hello"
        s = S.parse(original)
        assert s.length == 5
        assert s.data == b"Hello"

        # Modify payload
        s.data = b"Hi"

        # Sync and serialize
        new_raw = s.sync().to_bytes()
        assert new_raw == bytes([2, 0x48, 0x69])  # length=2, "Hi"
