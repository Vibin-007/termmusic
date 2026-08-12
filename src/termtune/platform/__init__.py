"""Platform adapter detection and factory."""

import platform
from termtune.platform.base import BasePlatformAdapter
from termtune.platform.linux import LinuxPlatformAdapter
from termtune.platform.macos import MacOSPlatformAdapter
from termtune.platform.windows import WindowsPlatformAdapter


def get_platform_adapter() -> BasePlatformAdapter:
    """Return OS-specific platform adapter instance."""
    sys_name = platform.system().lower()
    if sys_name == "windows":
        return WindowsPlatformAdapter()
    elif sys_name == "darwin":
        return MacOSPlatformAdapter()
    else:
        return LinuxPlatformAdapter()


__all__ = [
    "BasePlatformAdapter",
    "LinuxPlatformAdapter",
    "WindowsPlatformAdapter",
    "MacOSPlatformAdapter",
    "get_platform_adapter",
]
