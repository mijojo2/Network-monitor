import customtkinter as ctk
import threading
import time
import concurrent.futures
from PIL import Image
from scanner import ping
from device_card import DeviceCard
from storage import load_devices, save_devices
from models import Device, get_default_sub_devices


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class NetworkMonitor(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Network Monitor - Devices & Sub-devices")
        self.geometry("1060x700")
        self.minsize(900, 550)

        try:
            self.bg_image = ctk.CTkImage(
                light_image=Image.open("assets/background.png"),
                dark_image=Image.open("assets/background.png"),
                size=(1060, 700)
            )
            self.background = ctk.CTkLabel(
                self,
                image=self.bg_image,
                text=""
            )
            self.background.place(
                x=0,
                y=0,
                relwidth=1,
                relheight=1
            )
        except Exception:
            self.configure(fg_color="#0B132B")

        self.cards = []
        self.stop_requested = False
        self.is_scanning = False
        self._is_updating_order = False
        self.all_expanded = False

        self.build_gui()
        self.load_cards()

    def build_gui(self):
        top = ctk.CTkFrame(
            self,
            fg_color="#1E293B",
            corner_radius=12,
            border_width=1,
            border_color="#334155"
        )
        top.pack(fill="x", padx=12, pady=(10, 5))

        # Add Device Section
        self.name_entry = ctk.CTkEntry(
            top,
            placeholder_text="Device Name",
            width=160,
            height=32
        )
        self.name_entry.pack(side="left", padx=(10, 4), pady=8)
        self.name_entry.bind("<Return>", lambda e: self.ip_entry.focus_set())

        self.ip_entry = ctk.CTkEntry(
            top,
            placeholder_text="IP Address",
            width=140,
            height=32
        )
        self.ip_entry.pack(side="left", padx=4, pady=8)
        self.ip_entry.bind("<Return>", lambda e: self.add_device())

        ctk.CTkButton(
            top,
            text="➕ Add",
            width=70,
            height=32,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.add_device
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkButton(
            top,
            text="🗑 Delete",
            width=75,
            height=32,
            fg_color="#DC2626",
            hover_color="#991B1B",
            command=self.delete_selected
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkButton(
            top,
            text="⚡ Ping Selected",
            width=115,
            height=32,
            fg_color="#059669",
            hover_color="#047857",
            command=self.ping_selected
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkButton(
            top,
            text="🛑 Stop",
            width=65,
            height=32,
            fg_color="#B91C1C",
            hover_color="#7F1D1D",
            command=self.stop_scan
        ).pack(side="left", padx=4, pady=8)

        # Quick Actions
        self.select_all_btn = ctk.CTkButton(
            top,
            text="Select All",
            width=85,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.toggle_select_all
        )
        self.select_all_btn.pack(side="left", padx=4, pady=8)

        self.expand_all_btn = ctk.CTkButton(
            top,
            text="Expand All",
            width=90,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.toggle_expand_all
        )
        self.expand_all_btn.pack(side="left", padx=4, pady=8)

        # Search Bar
        self.search = ctk.CTkEntry(
            top,
            placeholder_text="🔍 Search name or IP...",
            width=200,
            height=32
        )
        self.search.pack(side="right", padx=(4, 10), pady=8)
        self.search.bind("<KeyRelease>", self.search_devices)

        # Device Frame
        self.device_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F172A",
            corner_radius=12,
            border_width=1,
            border_color="#1E293B"
        )
        self.device_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(5, 12)
        )

        top.lift()
        self.device_frame.lift()

    def on_save_devices(self):
        save_devices([c.device for c in self.cards])

    def load_cards(self):
        devices = load_devices()

        for device in devices:
            card = DeviceCard(
                self.device_frame,
                device
            )
            card.selection_callback = self.refresh_card_order
            card.save_callback = self.on_save_devices

            card.pack(
                fill="x",
                padx=5,
                pady=5
            )

            self.cards.append(card)

    def add_device(self):
        name = self.name_entry.get().strip()
        ip = self.ip_entry.get().strip()

        if not name or not ip:
            return

        device = Device(
            name=name,
            ip=ip,
            sub_devices=get_default_sub_devices(ip)
        )

        card = DeviceCard(
            self.device_frame,
            device
        )

        card.selection_callback = self.refresh_card_order
        card.save_callback = self.on_save_devices

        card.pack(
            fill="x",
            padx=5,
            pady=5
        )

        self.cards.append(card)
        self.on_save_devices()

        self.name_entry.delete(0, "end")
        self.ip_entry.delete(0, "end")
        self.name_entry.focus_set()

    def delete_selected(self):
        remaining = []

        for card in self.cards:
            if card.is_selected():
                card.destroy()
            else:
                remaining.append(card)

        self.cards = remaining
        self.on_save_devices()

    def toggle_select_all(self):
        visible_cards = [c for c in self.cards if c.winfo_ismapped()]
        target_cards = visible_cards if visible_cards else self.cards
        if not target_cards:
            return

        any_unselected = any(not c.is_selected() for c in target_cards)

        # Silence individual callbacks during bulk update to prevent N*N layout repacks
        self._is_updating_order = True
        try:
            for c in target_cards:
                c.set_selected(any_unselected)
        finally:
            self._is_updating_order = False

        self.select_all_btn.configure(text="Deselect All" if any_unselected else "Select All")
        self.refresh_card_order()

    def toggle_expand_all(self):
        self.all_expanded = not self.all_expanded
        for card in self.cards:
            if self.all_expanded:
                card.expand()
            else:
                card.collapse()

        self.expand_all_btn.configure(text="Collapse All" if self.all_expanded else "Expand All")

    def stop_scan(self):
        self.stop_requested = True

    def ping_selected(self):
        self.stop_requested = False
        if not self.is_scanning:
            self.is_scanning = True
            threading.Thread(
                target=self._scan_coordinator,
                daemon=True
            ).start()

    def _scan_coordinator(self):
        """Centralized, high-throughput scanning loop with controlled concurrency."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            while not self.stop_requested:
                selected_cards = [c for c in self.cards if c.is_selected()]

                if not selected_cards:
                    time.sleep(0.5)
                    continue

                # Set checking indicator on selected cards
                for card in selected_cards:
                    if self.stop_requested:
                        break
                    self.after(0, card.set_checking)

                # Ping unit for a single card: pings parent IP and each sub-device IP
                def ping_one_card(card):
                    if self.stop_requested:
                        return None
                    parent_result = ping(card.device.ip)
                    sub_results = [ping(s.ip) for s in card.device.sub_devices]
                    return card, parent_result, sub_results

                # Submit all selected cards to the shared thread pool
                futures = {
                    executor.submit(ping_one_card, card): card
                    for card in selected_cards
                }

                # As each card completes, update its UI in a single atomic batch call
                for future in concurrent.futures.as_completed(futures):
                    if self.stop_requested:
                        break
                    try:
                        res = future.result()
                        if res:
                            card, p_res, s_res = res
                            self.after(
                                0,
                                lambda c=card, p=p_res, s=s_res: c.apply_ping_results(p, s)
                            )
                    except Exception:
                        pass

                if self.stop_requested:
                    break

                # Brief interval before next ping cycle
                time.sleep(1)

        self.is_scanning = False

    def search_devices(self, event=None):
        text = self.search.get().strip().lower()

        for card in self.cards:
            name = card.device.name.lower()
            ip = card.device.ip.lower()

            # Match parent name/ip or any sub-device name/ip
            sub_match = any(
                text in s.name.lower() or text in s.ip.lower()
                for s in card.device.sub_devices
            )

            if not text or text in name or text in ip or sub_match:
                if not card.winfo_ismapped():
                    card.pack(fill="x", padx=5, pady=5)
            else:
                if card.winfo_ismapped():
                    card.pack_forget()

    def refresh_card_order(self):
        if self._is_updating_order:
            return

        selected = [card for card in self.cards if card.is_selected()]
        unselected = [card for card in self.cards if not card.is_selected()]
        new_order = selected + unselected

        # Only repack if the order has actually changed (prevents freezing)
        if new_order == self.cards:
            return

        self._is_updating_order = True
        try:
            self.cards = new_order
            for card in self.cards:
                card.pack_forget()
            for card in self.cards:
                card.pack(fill="x", padx=5, pady=5)
        finally:
            self._is_updating_order = False