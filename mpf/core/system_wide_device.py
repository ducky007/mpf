"""A system wide device which can be defined in the main config."""
import abc

from mpf.core.device import Device


class SystemWideDevice(Device, metaclass=abc.ABCMeta):

    """A system wide device which can be defined in the main config."""

    def device_added_system_wide(self):
        """Called when a device is added system wide."""
        self._initialize()
