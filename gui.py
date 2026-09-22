import customtkinter as ctk
import threading
import time
from PIL import Image
from scanner import ping
from device_card import DeviceCard
from storage import load_devices, save_devices
from models import Device

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class NetworkMonitor(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Network Monitor")
        self.geometry("1000x650")
        self.bg_image = ctk.CTkImage(
            light_image=Image.open("assets/background.png"),
            dark_image=Image.open("assets/background.png"),
            size=(1000, 650)
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

        self.cards = []
        self.stop_requested = False

        self.build_gui()
        self.load_cards()

    def build_gui(self):

        top = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        top.pack(fill="x", padx=10, pady=10)

        self.name_entry = ctk.CTkEntry(
            top,
            placeholder_text="Device Name",
            width=180
        )
        self.name_entry.pack(side="left", padx=5)

        self.ip_entry = ctk.CTkEntry(
            top,
            placeholder_text="IP Address",
            width=150
        )
        self.ip_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            top,
            text="Add",
            command=self.add_device
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            top,
            text="Delete",
            command=self.delete_selected
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            top,
            text="Ping Selected",
            command=self.ping_selected
        ).pack(side="left", padx=5)


        ctk.CTkButton(
            top,
            text="Stop",
            fg_color="red",
            hover_color="#990000",
            command=self.stop_scan
        ).pack(side="left", padx=5)

        self.search = ctk.CTkEntry(
            top,
            placeholder_text="Search...",
            width=180
        )

        self.search.pack(side="right", padx=5)

        self.search.bind("<KeyRelease>", self.search_devices)

        self.device_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F172A",  # or "#111827"
            corner_radius=15
        )
        self.device_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )
        top.lift()
        self.device_frame.lift()

    def load_cards(self):

        devices = load_devices()

        for device in devices:
            card = DeviceCard(
                self.device_frame,
                device
            )

            card.selection_callback = self.refresh_card_order

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
            ip=ip
        )

        card = DeviceCard(
            self.device_frame,
            device
        )

        card.selection_callback = self.refresh_card_order

        card.pack(
            fill="x",
            padx=5,
            pady=5
        )

        self.cards.append(card)

        save_devices([c.device for c in self.cards])

        self.name_entry.delete(0, "end")
        self.ip_entry.delete(0, "end")

    def delete_selected(self):

        remaining = []

        for card in self.cards:

            if card.is_selected():
                card.destroy()
            else:
                remaining.append(card)

        self.cards = remaining

        save_devices([c.device for c in self.cards])

    def ping_card(self, card):

        while not self.stop_requested:

            self.after(0, card.set_checking)

            online, latency = ping(card.device.ip)

            if self.stop_requested:
                break

            self.after(
                0,
                lambda o=online, l=latency: card.update_status(
                    o,
                    l
                )
            )

            time.sleep(1)

    def stop_scan(self):
        self.stop_requested = True


    def ping_selected(self):

        self.stop_requested = False

        for card in self.cards:

            if card.is_selected():

                threading.Thread(
                    target=self.ping_card,
                    args=(card,),
                    daemon=True
                ).start()

    def stop_scan(self):

        self.stop_requested = True

    def search_devices(self, event=None):

        text = self.search.get().lower()

        for card in self.cards:

            name = card.device.name.lower()
            ip = card.device.ip.lower()

            if text in name or text in ip:

                if not card.winfo_ismapped():
                    card.pack(fill="x", padx=5, pady=5)

            else:

                if card.winfo_ismapped():
                    card.pack_forget()

    def refresh_card_order(self):

        # Remove all cards from the layout
        for card in self.cards:
            card.pack_forget()

        # Checked cards first
        selected = [card for card in self.cards if card.is_selected()]

        # Then unchecked cards
        unselected = [card for card in self.cards if not card.is_selected()]

        # Display in the new order
        for card in selected + unselected:
            card.pack(fill="x", padx=5, pady=5)

    def ping_loop(self):

        while not self.stop_requested:

            threads = []

            for card in self.cards:
                thread = threading.Thread(
                    target=self.ping_card,
                    args=(card,),
                    daemon=True
                )

                thread.start()
                threads.append(thread)

            # Wait until every ping finishes
            for thread in threads:
                thread.join()

            # Wait 2 seconds before scanning again
            time.sleep(1)