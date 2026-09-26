# Changelog

All notable changes to the **Network Monitor** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Planned / In Progress
- Continuous improvements to device monitoring and alerts.
- Automated commit & changelog tracking workflow.

---

## [1.1.0] - 2026-09-25
### Added
- **Sub-Devices Architecture**:
  - Introduced `SubDevice` dataclass in [`models.py`](models.py) with attributes `name`, `ip`, `status`, and `latency`.
  - Added helper `get_default_sub_devices(ip)` that automatically generates default branch sub-devices:
    - Fingerprint (`.201`)
    - Cash 1 (`.3`)
    - Cash 2 (`.4`)
    - Manager (`.5`)
  - Extended `Device` dataclass to include a list of `sub_devices` with automatic validation in `__post_init__`.
- **Sub-Devices GUI & Accordion View**:
  - Expanded [`device_card.py`](device_card.py) to support collapsible/expandable sub-device lists under each parent device card.
  - Added sub-device status indicators with distinct colors (Online: green, Offline: red, Unknown: gray) and latency metrics.
  - Added bulk expand/collapse controls across all cards.
- **High-Performance Native Win32 ICMP Ping**:
  - Re-architected [`scanner.py`](scanner.py) with native Windows ICMP API (`iphlpapi.dll` via `ctypes`): `IcmpCreateFile`, `IcmpSendEcho`, and `IcmpCloseHandle`.
  - Achieved zero-lag scanning without spawning OS processes for each ping.
  - Maintained cross-platform fallback using standard `subprocess` ping for non-Windows environments.
- **Nested JSON Storage**:
  - Updated [`storage.py`](storage.py) to read and persist sub-devices in `devices.JSON` with UTF-8 encoding support.

### Changed
- **Concurrent Scanning**:
  - Upgraded scanning loop in [`gui.py`](gui.py) with `concurrent.futures.ThreadPoolExecutor` to scan both devices and their sub-devices simultaneously without blocking the UI thread.
- **UI Enhancements**:
  - Modernized card layouts with refined typography, badges, and responsive controls.

---

## [1.0.0] - 2026-09-20
### Added
- **Initial Release**:
  - Modern CustomTkinter desktop interface for network device monitoring.
  - Basic ping scanner with latency tracking and status detection.
  - Device card list with dynamic loading from `devices.json`.
  - PyInstaller build configuration ([`main.spec`](main.spec)).
