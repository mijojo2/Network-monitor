# Backward compatibility wrapper for core.models
from core.models import Device, SubDevice, NetworkStats, get_default_sub_devices

__all__ = ["Device", "SubDevice", "NetworkStats", "get_default_sub_devices"]