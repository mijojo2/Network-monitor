# Backward compatibility wrapper for services.storage_service
from services.storage_service import StorageService

_default_storage = StorageService()

load_devices = _default_storage.load_devices
save_devices = _default_storage.save_devices

__all__ = ["StorageService", "load_devices", "save_devices"]