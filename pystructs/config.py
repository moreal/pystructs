"""Global configuration for pystructs."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = (
    "GlobalConfig",
    "Endian",
    "get_config",
    "configure",
)


class Endian:
    """Endianness constants."""

    LITTLE = "little"
    BIG = "big"
    NATIVE = "native"
    NETWORK = "big"  # Network byte order is big-endian


@dataclass
class GlobalConfig:
    """Global configuration options."""

    default_endian: str = field(default=Endian.LITTLE)


_global_config = GlobalConfig()


def get_config() -> GlobalConfig:
    """Get the global configuration."""
    return _global_config


def configure(**kwargs) -> None:
    """Configure global options.

    Args:
        default_endian: Default endianness for all structs ('little' or 'big')
    """
    global _global_config
    if "default_endian" in kwargs:
        _global_config.default_endian = kwargs["default_endian"]
