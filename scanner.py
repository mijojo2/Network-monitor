# Backward compatibility wrapper for services.scanner_service
from services.scanner_service import ScannerService, ping

__all__ = ["ScannerService", "ping"]