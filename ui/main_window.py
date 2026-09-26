import customtkinter as ctk
import threading
import time
import concurrent.futures
from tkinter import filedialog, messagebox
from typing import List, Optional
from PIL import Image

from core.models import Device, NetworkStats, get_default_sub_devices
from services.scanner_service import ScannerService, ping, scan_device_hierarchy
from services.storage_service import StorageService
from services.excel_service import ExcelService
from services.alert_service import AlertService
from ui.theme import Theme
from ui.components.device_card import DeviceCard
from ui.components.stats_bar import StatsBar
from ui.components.filter_bar import FilterBar


class NetworkMonitorApp(ctk.CTk):
    """
    Main Application Window built on Clean Architecture, Reactive State-Diffing,
    and Smart Hierarchical Scanning with Anti-Flapping verification.
    """

    def __init__(self):
        super().__init__()

        # Services
        self.storage_service = StorageService()
        self.scanner_service = ScannerService(timeout_ms=700)
        self.alert_service = AlertService(sound_enabled=True)

        # Persistent Thread Pool
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)

        # State
        self.cards: List[DeviceCard] = []
        self.stop_requested = False
        self.is_scanning = False
        self.scan_mode = "ALL"  # "ALL" or "SELECTED"
        self.all_expanded = False
        self.active_status_filter = "ALL"  # "ALL", "ONLINE", "OFFLINE", "SUB_ISSUES"
        self.active_type_filter = "ALL"    # "ALL", "CIRCLE_K", "FRANCHISE"
        self.active_sort = "LATEST"        # "LATEST", "NAME"
        self._search_after_id = None
        self._previous_states = {}  # Tracks IP -> status for offline alerts
        self._session_active_branches = set()  # Only branches active in this session can trigger drop alerts

        self._init_window()
        self._build_gui()
        self.load_devices()

        # Handle clean window closing
        self.protocol("WM_DELETE_WINDOW", self._on_window_closing)

        # Auto-start scanning on launch (after UI has fully rendered)
        self.after(500, self.start_auto_scan)

    def _init_window(self):
        self.title("Network Monitor Pro - Multi-Branch & Sub-Devices")
        self.geometry("1140x740")
        self.minsize(960, 600)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        try:
            self.bg_image = ctk.CTkImage(
                light_image=Image.open("assets/background.png"),
                dark_image=Image.open("assets/background.png"),
                size=(1140, 740)
            )
            self.background = ctk.CTkLabel(self, image=self.bg_image, text="")
            self.background.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            self.configure(fg_color=Theme.BG_DARK)

    def _on_window_closing(self):
        self.stop_requested = True
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self.destroy()

    def _build_gui(self):
        # 1. Top Action Toolbar
        top_bar = ctk.CTkFrame(
            self,
            fg_color=Theme.PANEL_BG,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER_COLOR
        )
        top_bar.pack(fill="x", padx=12, pady=(10, 5))

        # Add Device Section
        self.name_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Branch Name",
            width=140,
            height=32
        )
        self.name_entry.pack(side="left", padx=(10, 3), pady=8)
        self.name_entry.bind("<Return>", lambda e: self.ip_entry.focus_set())

        self.ip_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Router IP (.1)",
            width=130,
            height=32
        )
        self.ip_entry.pack(side="left", padx=3, pady=8)
        self.ip_entry.bind("<Return>", lambda e: self.add_device())

        ctk.CTkButton(
            top_bar,
            text="➕ Add",
            width=65,
            height=32,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=self.add_device
        ).pack(side="left", padx=3, pady=8)

        ctk.CTkButton(
            top_bar,
            text="🗑 Delete",
            width=70,
            height=32,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color=Theme.ACCENT_RED,
            hover_color=Theme.ACCENT_RED_HOVER,
            command=self.delete_selected
        ).pack(side="left", padx=3, pady=8)

        # Scanning Controls: Scan All & Scan Selected & Stop
        self.scan_all_btn = ctk.CTkButton(
            top_bar,
            text="⚡ Scan All",
            width=100,
            height=32,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            command=self.start_scan_all
        )
        self.scan_all_btn.pack(side="left", padx=3, pady=8)

        self.scan_selected_btn = ctk.CTkButton(
            top_bar,
            text="🎯 Scan Selected",
            width=115,
            height=32,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.start_scan_selected
        )
        self.scan_selected_btn.pack(side="left", padx=3, pady=8)

        self.stop_btn = ctk.CTkButton(
            top_bar,
            text="🛑 Stop",
            width=65,
            height=32,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color="#B91C1C",
            hover_color="#7F1D1D",
            command=self.stop_scan
        )
        self.stop_btn.pack(side="left", padx=3, pady=8)

        # Bulk Expand & Select Actions
        self.select_all_btn = ctk.CTkButton(
            top_bar,
            text="Select All",
            width=80,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.toggle_select_all
        )
        self.select_all_btn.pack(side="left", padx=3, pady=8)

        self.expand_all_btn = ctk.CTkButton(
            top_bar,
            text="Expand All",
            width=85,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.toggle_expand_all
        )
        self.expand_all_btn.pack(side="left", padx=3, pady=8)

        # Import & Export Buttons
        ctk.CTkButton(
            top_bar,
            text="📥 Export",
            width=70,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.export_excel
        ).pack(side="left", padx=3, pady=8)

        ctk.CTkButton(
            top_bar,
            text="📤 Import",
            width=70,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.import_excel
        ).pack(side="left", padx=3, pady=8)

        # Search Bar
        self.search = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Search name or IP...",
            width=160,
            height=32
        )
        self.search.pack(side="right", padx=(4, 10), pady=8)
        self.search.bind("<KeyRelease>", self._on_search_keyrelease)

        # 2. Live Dashboard Stats Bar
        self.stats_bar = StatsBar(self, on_toggle_sound=self._on_toggle_sound)
        self.stats_bar.pack(fill="x", padx=12, pady=(0, 4))

        # 3. Quick Status & Type Filter Bar (With Sub Issues, Circle K, Franchise, and Sort)
        filter_container = ctk.CTkFrame(self, fg_color="transparent")
        filter_container.pack(fill="x", padx=12, pady=(2, 4))
        self.filter_bar = FilterBar(filter_container, on_filter_change=self._on_filter_changed)
        self.filter_bar.pack(fill="x", expand=True)

        # 4. Scrollable Device Cards Container
        self.device_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.CONTAINER_BG,
            corner_radius=10,
            border_width=1,
            border_color="#1E293B"
        )
        self.device_frame.pack(fill="both", expand=True, padx=12, pady=(2, 10))

    def _on_toggle_sound(self, enabled: bool):
        self.alert_service.sound_enabled = enabled

    def _on_filter_changed(self, status_filter: str, type_filter: str, sort_type: str):
        self.active_status_filter = status_filter
        self.active_type_filter = type_filter
        self.active_sort = sort_type
        self._apply_display_filters()

    def _on_search_keyrelease(self, event=None):
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(180, self._apply_display_filters)

    def _card_matches_filter_and_search(self, card: DeviceCard) -> bool:
        """Determines if a card matches status filter, branch type, and search query."""
        dev = card.device
        filter_mode = self.active_status_filter
        offline_subs_count = sum(1 for s in dev.sub_devices if s.status == "Offline")

        # 1. Status Filter Tab Logic
        if filter_mode == "ONLINE" and dev.status != "Online":
            return False
        elif filter_mode == "OFFLINE" and dev.status != "Offline":
            return False
        elif filter_mode == "SUB_ISSUES" and not (dev.status == "Online" and offline_subs_count >= 2):
            return False

        # 2. Branch Type Filter Logic (Circle K vs Franchise)
        b_type = dev.get_branch_type()
        if self.active_type_filter == "CIRCLE_K" and b_type != "CircleK":
            return False
        elif self.active_type_filter == "FRANCHISE" and b_type != "Franchise":
            return False

        # 3. Search Query Logic
        query = self.search.get().strip().lower()
        if query:
            name_match = query in dev.name.lower()
            ip_match = query in dev.ip.lower()
            sub_match = any(
                query in s.name.lower() or query in s.ip.lower()
                for s in dev.sub_devices
            )
            return (name_match or ip_match or sub_match)

        return True

    def _check_card_filter_visibility(self, card: DeviceCard):
        """Dynamically adjusts a single card's visibility when its ping state updates."""
        should_show = self._card_matches_filter_and_search(card)
        is_mapped = card.winfo_ismapped()
        if should_show and not is_mapped:
            card.pack(fill="x", padx=5, pady=4)
        elif not should_show and is_mapped:
            card.pack_forget()

    def _get_card_sort_key(self, card: DeviceCard):
        """
        Sort order:
        - LATEST: Cards with recorded last_seen come first (-last_seen DESC), unrecorded alphabetically.
        - NAME: Cards sorted alphabetically by branch name (A-Z).
        """
        dev = card.device
        if self.active_sort == "LATEST":
            if dev.last_seen is not None and dev.last_seen > 0:
                return (0, -dev.last_seen, dev.name.lower())
            else:
                return (1, 0, dev.name.lower())
        else:
            return (0, 0, dev.name.lower())

    def _apply_display_filters(self):
        """Filters and repacks cards in sorted order."""
        matching_cards = []
        for card in self.cards:
            if self._card_matches_filter_and_search(card):
                matching_cards.append(card)
            else:
                if card.winfo_ismapped():
                    card.pack_forget()

        # Sort matching cards according to active sort option
        matching_cards.sort(key=self._get_card_sort_key)

        # Unpack matching then repack to guarantee exact visual order
        for card in matching_cards:
            card.pack_forget()
        for card in matching_cards:
            card.pack(fill="x", padx=5, pady=4)

    def load_devices(self):
        for card in self.cards:
            card.destroy()
        self.cards = []

        devices = self.storage_service.load_devices()
        for dev in devices:
            self._create_and_pack_card(dev)

        self._refresh_stats()

    def _create_and_pack_card(self, device: Device) -> DeviceCard:
        card = DeviceCard(
            self.device_frame,
            device,
            on_update=self._on_device_updated,
            on_selection_change=self._refresh_stats
        )
        card.pack(fill="x", padx=5, pady=4)
        self.cards.append(card)
        return card

    def _on_device_updated(self):
        self.storage_service.save_devices([c.device for c in self.cards])
        self._refresh_stats()

    def _refresh_stats(self):
        total = len(self.cards)
        online = sum(1 for c in self.cards if c.device.status == "Online")
        offline = sum(1 for c in self.cards if c.device.status == "Offline")
        sub_issues = sum(
            1 for c in self.cards
            if c.device.status == "Online" and sum(1 for s in c.device.sub_devices if s.status == "Offline") >= 2
        )
        unknown = total - (online + offline)

        circle_k = sum(1 for c in self.cards if c.device.get_branch_type() == "CircleK")
        franchise = sum(1 for c in self.cards if c.device.get_branch_type() == "Franchise")

        target_scope = total
        if self.scan_mode == "SELECTED":
            selected_count = sum(1 for c in self.cards if c.is_selected())
            if selected_count > 0:
                target_scope = selected_count

        stats = NetworkStats(
            total_devices=total,
            online_devices=online,
            offline_devices=offline,
            checking_devices=0,
            unknown_devices=unknown
        )
        self.stats_bar.update_stats(stats, target_scope)
        self.filter_bar.update_counts(total, online, offline, sub_issues, circle_k, franchise)

        # Refresh sorted display order so newly updated cards float smoothly
        self._apply_display_filters()

    def add_device(self):
        name = self.name_entry.get().strip()
        ip = self.ip_entry.get().strip()
        if not name or not ip:
            return

        # Ensure router IP ends in .1
        parts = ip.split('.')
        if len(parts) == 4 and parts[3] != '1':
            parts[3] = '1'
            ip = '.'.join(parts)

        device = Device(
            name=name,
            ip=ip,
            sub_devices=get_default_sub_devices(ip)
        )
        self._create_and_pack_card(device)
        self._on_device_updated()

        self.name_entry.delete(0, "end")
        self.ip_entry.delete(0, "end")
        self.name_entry.focus_set()

    def delete_selected(self):
        remaining = []
        deleted_count = 0
        for card in self.cards:
            if card.is_selected():
                card.destroy()
                deleted_count += 1
            else:
                remaining.append(card)

        if deleted_count > 0:
            self.cards = remaining
            self._on_device_updated()

    def toggle_select_all(self):
        visible = [c for c in self.cards if c.winfo_ismapped()]
        target = visible if visible else self.cards
        if not target:
            return

        any_unselected = any(not c.is_selected() for c in target)
        for c in target:
            c.set_selected(any_unselected)

        self.select_all_btn.configure(text="Deselect All" if any_unselected else "Select All")
        self._refresh_stats()

    def toggle_expand_all(self):
        self.all_expanded = not self.all_expanded
        for card in self.cards:
            if self.all_expanded:
                card.expand()
            else:
                card.collapse()
        self.expand_all_btn.configure(text="Collapse All" if self.all_expanded else "Expand All")

    # ==========================================
    # SCANNING CONTROLS & SMART HIERARCHICAL SCANNER
    # ==========================================

    def start_auto_scan(self):
        """Automatically begins monitoring all branches on launch."""
        if not self.is_scanning:
            self.start_scan_all()

    def start_scan_all(self):
        """Monitors all registered branches in continuous silent background mode."""
        self.scan_mode = "ALL"
        self.stop_requested = False
        self._update_button_visuals(running_mode="ALL")

        if hasattr(self, "_scan_wake_event"):
            self._scan_wake_event.set()

        if not self.is_scanning:
            self.is_scanning = True
            threading.Thread(target=self._reactive_scan_coordinator, daemon=True).start()

    def start_scan_selected(self):
        """Monitors only the specifically selected branches."""
        selected_cards = [c for c in self.cards if c.is_selected()]
        if not selected_cards:
            messagebox.showinfo("Selection Required", "Please check at least one device checkbox to scan selected.")
            return

        self.scan_mode = "SELECTED"
        self.stop_requested = False
        self._update_button_visuals(running_mode="SELECTED")

        if hasattr(self, "_scan_wake_event"):
            self._scan_wake_event.set()

        if not self.is_scanning:
            self.is_scanning = True
            threading.Thread(target=self._reactive_scan_coordinator, daemon=True).start()

    def stop_scan(self):
        """Stops the scanning engine immediately."""
        self.stop_requested = True
        self._update_button_visuals(running_mode="STOPPED")
        self.stats_bar.update_progress(0, 0, status_text="🛑 Stopped")

    def _update_button_visuals(self, running_mode: str):
        if running_mode == "ALL":
            self.scan_all_btn.configure(text="⚡ Scanning All...", fg_color="#F59E0B")
            self.scan_selected_btn.configure(text="🎯 Scan Selected", fg_color="#0284C7")
        elif running_mode == "SELECTED":
            self.scan_all_btn.configure(text="⚡ Scan All", fg_color=Theme.ACCENT_GREEN)
            self.scan_selected_btn.configure(text="🎯 Scanning Sel...", fg_color="#F59E0B")
        else:
            self.scan_all_btn.configure(text="⚡ Scan All", fg_color=Theme.ACCENT_GREEN)
            self.scan_selected_btn.configure(text="🎯 Scan Selected", fg_color="#0284C7")

    def _dispatch_ping_batch(self, batch, completed: int, total: int):
        """
        Dispatches an entire batch of ping results in a single UI tick.
        Dynamically adjusts card filter presence so online branches don't linger in offline tab.
        """
        def _apply():
            for card, p_res, s_res in batch:
                card.apply_ping_results(p_res, s_res)
                # Keep active filter view accurate in real time
                if self.active_status_filter != "ALL":
                    self._check_card_filter_visibility(card)
            self.stats_bar.update_progress(completed, total)
        self.after(0, _apply)

    def _reactive_scan_coordinator(self):
        """
        Smart Reactive Scanner:
        1. Hierarchical ping: If router is down, immediately marks sub-devices down (skips 5 timeouts).
        2. Anti-flapping: Confirms timeouts with immediate retry to eliminate false drops.
        3. Batched dispatches: Smooth 60 FPS UI without main-thread flooding.
        4. Smooth Cadence: 8s calm breathing interval with live countdown and confirmed audio alerts.
        """
        self._offline_failure_counts = {}
        self._scan_cycle_count = 0
        self._scan_wake_event = threading.Event()

        while not self.stop_requested:
            if self.scan_mode == "SELECTED":
                target_cards = [c for c in self.cards if c.is_selected()]
            else:
                target_cards = self.cards

            total_in_cycle = len(target_cards)
            if total_in_cycle == 0:
                time.sleep(0.5)
                continue

            completed_in_cycle = 0

            # Smart hierarchical ping task
            def ping_card_unit(card: DeviceCard):
                if self.stop_requested:
                    return None
                sub_ips = [s.ip for s in card.device.sub_devices]
                p_res, s_res = scan_device_hierarchy(card.device.ip, sub_ips, timeout_ms=700)
                return card, p_res, s_res

            futures = {
                self.executor.submit(ping_card_unit, card): card
                for card in target_cards
            }

            batch = []

            for future in concurrent.futures.as_completed(futures):
                if self.stop_requested:
                    break

                try:
                    res = future.result()
                    if res:
                        card, p_res, s_res = res
                        completed_in_cycle += 1

                        # Anti-flapping confirmed alert: only trigger if confirmed down across 2 cycles!
                        prev_status = self._previous_states.get(card.device.ip, "Unknown")
                        new_online, _ = p_res

                        if new_online:
                            self._offline_failure_counts[card.device.ip] = 0
                            self._previous_states[card.device.ip] = "Online"
                            self._session_active_branches.add(card.device.ip)
                        else:
                            failures = self._offline_failure_counts.get(card.device.ip, 0) + 1
                            self._offline_failure_counts[card.device.ip] = failures
                            # Alert ONLY when a branch that was active in this session drops for 2 confirmed cycles
                            if card.device.ip in self._session_active_branches and failures == 2:
                                self.alert_service.trigger_offline_alert(card.device.name, card.device.ip)
                                self._session_active_branches.discard(card.device.ip)
                            if failures >= 2:
                                self._previous_states[card.device.ip] = "Offline"

                        batch.append((card, p_res, s_res))

                        if len(batch) >= 12:
                            self._dispatch_ping_batch(list(batch), completed_in_cycle, total_in_cycle)
                            batch.clear()
                except Exception:
                    pass

            if batch and not self.stop_requested:
                self._dispatch_ping_batch(list(batch), completed_in_cycle, total_in_cycle)

            if self.stop_requested:
                break

            # Cycle complete: atomic stats refresh
            self.after(0, self._refresh_stats)
            self._scan_cycle_count += 1

            # Auto-save last seen timestamps every 3 cycles
            if self._scan_cycle_count % 3 == 0:
                self.storage_service.save_devices([c.device for c in self.cards])

            # Smooth resting cadence (8 seconds countdown)
            for sec in range(8, 0, -1):
                if self.stop_requested:
                    break
                self.after(0, lambda s=sec: self.stats_bar.update_progress(0, 0, status_text=f"⏳ Next scan in {s}s"))
                for _ in range(10):
                    if self.stop_requested or (hasattr(self, "_scan_wake_event") and self._scan_wake_event.is_set()):
                        break
                    time.sleep(0.1)
                if hasattr(self, "_scan_wake_event") and self._scan_wake_event.is_set():
                    self._scan_wake_event.clear()
                    break

        self.is_scanning = False
        try:
            self.after(0, lambda: self._update_button_visuals(running_mode="STOPPED"))
        except Exception:
            pass

    # ==========================================
    # IMPORT & EXPORT
    # ==========================================

    def export_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("CSV UTF-8", "*.csv")],
            title="Export Devices"
        )
        if not file_path:
            return

        devices = [c.device for c in self.cards]
        if file_path.lower().endswith(".xlsx"):
            success, msg = ExcelService.export_to_excel(devices, file_path)
        else:
            success, msg = ExcelService.export_to_csv(devices, file_path)

        if success:
            messagebox.showinfo("Export Successful", msg)
        else:
            messagebox.showerror("Export Failed", msg)

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel or CSV", "*.xlsx;*.csv"), ("Excel Workbook", "*.xlsx"), ("CSV", "*.csv")],
            title="Import Devices"
        )
        if not file_path:
            return

        success, imported_devices, msg = ExcelService.import_from_file(file_path)
        if not success:
            messagebox.showerror("Import Failed", msg)
            return

        answer = messagebox.askyesno(
            "Confirm Import",
            f"{msg}\nDo you want to append these devices to your current list? (Click 'No' to replace current list)"
        )

        if answer:
            existing_ips = {c.device.ip for c in self.cards}
            for d in imported_devices:
                if d.ip not in existing_ips:
                    self._create_and_pack_card(d)
        else:
            for c in self.cards:
                c.destroy()
            self.cards = []
            for d in imported_devices:
                self._create_and_pack_card(d)

        self._on_device_updated()
        messagebox.showinfo("Import Complete", f"Successfully loaded devices into Network Monitor!")
