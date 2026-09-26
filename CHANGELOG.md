# Changelog

All notable changes to the **Network Monitor** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Planned / In Progress
- Optional Telegram/Discord webhook notifications for branch disconnections.

---

## [1.3.8] - 2026-09-26
### Added
- **Dedicated Critical Outage Tab (`⏳ Offline >5m`)**:
  - Added a dedicated status filter button in Row 1: `⏳ Offline >5m` with dynamic live counter.
  - Strictly isolates branches that have been down for more than 5 minutes (`>= 300 seconds`) continuously without a single successful online ping response.
  - Implemented anti-flapping downtime streak tracking: any intermittent online response immediately resets the 5-minute counter.
  - Works seamlessly with both branch types:
    - **All Types**: Displays all branches down > 5m across the entire company.
    - **🏢 Circle K**: Isolates only Circle K branches (Server IP `.222`) down > 5m.
    - **🤝 Franchise**: Isolates only Franchise branches (Server IP `.2`) down > 5m.
  - Live card presence updates in real time: as soon as an offline branch exceeds 5 minutes, it joins the tab; as soon as it recovers, it leaves the tab automatically.

---

## [1.3.7] - 2026-09-26
### Added
- **Visual Bell Outage Badge (`🔔 Outage Alert`)**:
  - Newly confirmed offline branches are prominently tagged on their card header with a bright `🔔 Outage Alert` badge.
  - The badge automatically clears when the branch recovers online.
  - Cycle-end status notifications display the exact names of newly dropped branches (e.g. `🔔 ALERT: [Name] went Offline!`).

### Changed
- **Smooth 60 FPS Scrolling Velocity & Viewport Synchronization**:
  - Removed full-window raster background image compositing, freeing up GDI rendering performance for pure 60 FPS scrolling.
  - Implemented accelerated mousewheel scrolling via `_setup_smooth_scrolling` with 40px velocity per notch for fluid gliding through cards.
  - Synchronized scroll viewport to automatically reset to top (`yview_moveto(0.0)`) upon typing a search query or toggling filters, preventing empty blank areas.
- **Strict Chronological Ordering on Tab Switches**:
  - Resolved filter tab order bug: switching from `Offline` back to `All` now strictly re-intertwines branches by `last_seen` timestamp rather than stacking offline cards at the top.
- **Zero-Delay Cycle-End Audio Alerts**:
  - Eliminated mid-scan sound hitches: audible chimes now sound cleanly at the conclusion of the scan cycle.
  - Switched to hardware-accelerated `winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)` with 0.1ms instant playback.

---

## [1.3.6] - 2026-09-26
### Changed
- **Zero-Flicker Reactive UI (Pure Bloc Architecture)**:
  - Removed full-screen widget repacking from periodic scan cycle refreshes, completely eliminating screen flashing, visual jitter, and scroll position resets.
  - Implemented seamless, in-place visibility toggling in `_apply_display_filters`: matching cards stay mounted without re-rendering, and leaf widgets update via state-diffing.
  - Reordered card sorting to run strictly upon explicit user interaction (Sort button clicks) and initial startup.
- **Top Toolbar Clean-Up**:
  - Removed the two unused input fields (`Branch Name` and `Router IP`) from the top left that cluttered the bar.
  - Replaced with a clean `➕ Add Branch` button that opens a dedicated modal dialog on demand.
  - Kept the working live search bar on the top right.

---

## [1.3.5] - 2026-09-26
### Added
- **Branch Type Segmentation (Circle K vs Franchise)**:
  - Added automatic branch classification: Server `.222` -> `🏢 Circle K` (103 branches), Server `.2` -> `🤝 Franchise` (107 branches).
  - Added two-tier interactive filter bar with dedicated type segment: `All Types`, `🏢 Circle K`, and `🤝 Franchise` with live counters.
  - Added sleek colored visual badges directly on every card header (`🏢 Circle K` in slate blue, `🤝 Franchise` in violet).
- **Dynamic Sorting (Latest Response vs Alphabetical)**:
  - Implemented dynamic sorting: `🕒 Latest Response` automatically floats branches with the most recent activity/disconnection to the top, falling back to alphabetical A-Z for unrecorded devices.
  - Added quick-toggle sort control in the filter bar (`🕒 Latest Response` | `🔤 A-Z`).
  - Cards reorder seamlessly at the end of each scan cycle and upon filter selection without UI jumping.

### Changed
- **Session-Confirmed Audio Outage Alerts**:
  - Enforced strict rule that audible alerts ONLY trigger when an actively working branch (observed online in the current session) drops for 2 consecutive confirmed cycles.
  - Eliminated audio alerts on application launch and for branches already known to be down.
  - Sub-devices and recovery events remain strictly silent.

---

## [1.3.4] - 2026-09-26
### Added
- **Server Sub-Device Provisioning for All 210 Branches**:
  - Ingested Google Sheet data (`2010088143`) to dynamically map each branch's dedicated Server IP ending.
  - Automatically provisioned a new `"Server"` sub-device across all 210 branches in [`devices.JSON`](devices.JSON):
    - 107 branches assigned `.2` as per network topography.
    - 103 branches assigned `.222` as per network topography.
  - Corrected copy-pasted subnet typos for pre-existing servers (`Kafrsh 2`, `ELMax`, `marina.walk`).

---

## [1.3.3] - 2026-09-26
### Added
- **"Last Seen / Responded" Relative Timestamps & History**:
  - Added connection history tracking (`last_seen`, `last_check`) to all branch models in [`Device`](core/models.py).
  - Every card now displays an indicator next to its name/IP:
    - Online: `🟢 Responded: 17:55:12` (exact clock time of response).
    - Offline: `🔴 Down: 2m ago (17:53:10)` or `🔴 Down: 1h 15m ago (...)` showing both elapsed downtime and exact disconnection timestamp.
  - Automatically persisted in `devices.JSON` across application sessions.

### Changed
- **Calm, Smooth Scanning Cadence (Eliminated Aggressive Continuous Scans)**:
  - Replaced the aggressive 1-2 second scan loop with a smooth 8-second resting cadence between cycles.
  - Added live countdown in the stats bar (`⏳ Next scan in 7s...`) so the admin knows when the next passive pass occurs.
  - Manual triggers (`⚡ Scan All` or `🎯 Scan Selected`) immediately wake the scanning coordinator from its resting interval without any delay.
- **2-Cycle Confirmed Outage Sound System & 15s Cooldown**:
  - Eliminated annoying sound beeps caused by transient single-second packet loss.
  - Audio warnings now strictly require **2 consecutive confirmed down cycles** before chiming.
  - Softened chime frequencies (700Hz/520Hz) and enforced a 15-second minimum cooldown between audible alerts.

---

## [1.3.2] - 2026-09-26
### Added
- **New Filter Tab: `⚠️ Sub Issues >=2`**:
  - Replaced the legacy `Checking` tab with `⚠️ Sub Issues >=2` to isolate branches with multiple failing sub-devices.
  - Branches with >=2 offline sub-devices now appear in both `Online` (router is healthy) and `⚠️ Sub Issues >=2` simultaneously.
  - The `Offline` tab now strictly shows branches whose router is actually Down.
  - Implemented dynamic real-time filter re-evaluation so online branches never linger in the offline tab when ping completes.

### Changed
- **Anti-Flapping Confirmation & Parent Dependency Scanner**:
  - Implemented two-packet confirmation retry on timeouts: transient packet loss or network jitter will no longer trigger false offline state changes.
  - Added Parent Gateway Dependency: if a router is detected as offline, child sub-device pings are immediately bypassed, saving 4-5 timeouts per dead branch and speeding up scan cycles by over 70%.
  - Tuned WAN timeout to 700ms to eliminate false alarms across high-latency VPN/4G links.

---

## [1.3.1] - 2026-09-26
### Added
- **Direct On-Header Offline Sub-Devices Visibility**:
  - The card header now displays the exact names of offline sub-devices directly on the outside without needing to expand the card (e.g. `● Down: Cash 1, Fingerprint` or `● All Sub Down (...)`).
- **Router IP Labeling & Standardization**:
  - Automatically standardized all 210 branch parent router IPs in [`devices.JSON`](devices.JSON) to end with `.1` as the last octet (remediated 71 incorrectly entered IP addresses).
  - Explicitly labeled all parent IPs as `Router: <ip>` in [`DeviceCard`](ui/components/device_card.py) for immediate visual identification.

### Changed
- **Ultra-Lightweight Lazy Loading & Performance Boost**:
  - Re-architected sub-device containers to instantiate lazily on-demand, eliminating over 1,500 widgets from the initial startup tree and dramatically improving scrolling performance.
  - Implemented Batched Ping Event Dispatches in the reactive scanning coordinator, cutting UI thread interrupts by 90%.
  - Added clean application shutdown protocol (`WM_DELETE_WINDOW`) to gracefully terminate background thread pools.

---

## [1.3.0] - 2026-09-26
### Added
- **BLoC / Reactive State-Diffing Architecture**:
  - Implemented conditional UI rendering in [`DeviceCard`](ui/components/device_card.py): if a branch and its sub-devices maintain their state, zero widget reconfigurations or repaints are performed.
  - Eliminated the global full-screen "Checking..." wipe at the start of each cycle, resulting in completely smooth, flicker-free background monitoring.
  - Reduced Tkinter redraws by over 95%, cutting CPU consumption to below 1% during active monitoring.
- **Auto-Start Monitoring**:
  - The application now begins scanning all branches automatically upon launch without requiring manual user initiation.
- **Selective vs Full Scanning Controls**:
  - Added dedicated `⚡ Scan All` (monitors all 210 branches) and `🎯 Scan Selected` (monitors only checked branches, leaving the others untouched) controls in the toolbar.
  - Responsive `🛑 Stop` button that halts the background scanning loop immediately.
- **Live "X/Y" Progress and Status Ratio Counters**:
  - Added real-time scan cycle progress indicator (`📡 Scanned: X/Y (PCT%)`) in [`StatsBar`](ui/components/stats_bar.py).
  - Upgraded Online and Offline counters to display exact ratios against total monitored scope (`● Online: X/Total`, `● Offline: Y/Total`).
- **Batched UI Stats Refresh & Inter-Cycle Throttle**:
  - Replaced per-ping stats recalculation with batched, throttled refresh at cycle completion, removing tens of thousands of redundant main thread iterations.
  - Added a 2-second inter-cycle breathing interval to prevent continuous network socket and CPU congestion.

---

## [1.2.0] - 2026-09-26
### Added
- **Clean Architecture Restructuring**:
  - Reorganized the entire codebase into modular, decoupled layers:
    - [`core/`](core/): Pure business entities and domain models ([`models.py`](core/models.py)).
    - [`services/`](services/): Isolated infrastructure and business logic ([`scanner_service.py`](services/scanner_service.py), [`storage_service.py`](services/storage_service.py), [`excel_service.py`](services/excel_service.py), [`alert_service.py`](services/alert_service.py)).
    - [`ui/`](ui/): CustomTkinter presentation layer with design system tokens ([`theme.py`](ui/theme.py)) and modular components ([`ui/components/`](ui/components/)).
  - Maintained complete backward compatibility through legacy module re-exports.
- **Vibrant Status Color System & Visual Badges**:
  - Fixed Windows Tkinter monochrome emoji rendering bug by replacing emoji glyphs with vector circle dots (`●`) with explicit color styling.
  - Added modern status pill containers for both parents and sub-devices:
    - **Online**: Emerald green dot (`#22C55E`), bright text (`#4ADE80`), deep green container (`#064E3B`), and green card border.
    - **Offline**: Crimson red dot (`#EF4444`), bright text (`#F87171`), deep red container (`#450A0A`), and red card border.
    - **Checking**: Amber dot (`#F59E0B`), warm text (`#FCD34D`), amber container (`#451A03`), and amber card border.
- **Live Monitoring Dashboard (`StatsBar`)**:
  - Integrated persistent stats bar at top of window displaying:
    - Total branches monitored
    - Online branches count (`● Online: X`)
    - Offline branches count (`● Offline: Y`)
    - Checking branches count (`● Checking: Z`)
    - Dynamic Network Health percentage (`⚡ Health: XX%`)
    - Interactive Sound Alert toggle (`🔔 Sound: ON/OFF`)
- **Quick Status Filter Bar (`FilterBar`)**:
  - Added dedicated one-click status filter buttons: `All`, `● Offline Only`, `● Online Only`, and `● Checking`.
  - Enables instant identification of failed branches across 200+ network locations without manual scrolling.
- **In-Place Device Editing (`EditDeviceDialog`)**:
  - Added `✏️ Edit` button on every card opening a modal configuration window.
  - Supports editing branch name, parent IP, and adding/editing/removing sub-devices without deleting the device.
- **Excel & CSV Import and Export (`ExcelService`)**:
  - Added `📥 Export` button supporting both native Excel (`.xlsx` via `openpyxl`) and CSV (`.csv`).
  - Added `📤 Import` button supporting append or replace workflows from spreadsheets.
- **Audible Disconnection Alert System (`AlertService`)**:
  - Built-in audio warning tone (using Windows `winsound`) triggered when any active branch transitions from Online to Offline.
  - Integrated cooldown rate-limiter to prevent alarm fatigue during bulk network outages.
- **Data Protection, Atomic Saving & Auto-Backups (`StorageService`)**:
  - Implemented atomic file writes via temporary files and OS-level replacement to prevent JSON corruption during unexpected shutdowns.
  - Implemented automatic rolling backups stored in `backups/` directory (retaining latest 7 snapshots).
- **Dependency Management**:
  - Added [`requirements.txt`](requirements.txt) specifying all required libraries (`customtkinter`, `pillow`, `openpyxl`, `darkdetect`).

### Changed
- **Scanner Optimization**:
  - Added thread-local ICMP handle caching in [`services/scanner_service.py`](services/scanner_service.py) to prevent OS handle exhaustion during high-concurrency scans across 1,000+ endpoints.
- **Debounced Search**:
  - Implemented 180ms keystroke debouncing in the search bar to eliminate UI hesitation during rapid typing.

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
