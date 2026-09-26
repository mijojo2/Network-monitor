import customtkinter as ctk
from core.models import Device, SubDevice
from ui.theme import Theme


class EditDeviceDialog(ctk.CTkToplevel):
    """Modal dialog allowing editing device details and its sub-devices."""

    def __init__(self, master, device: Device, on_saved=None):
        super().__init__(master)
        self.device = device
        self.on_saved = on_saved

        self.title(f"Edit Device - {device.name}")
        self.geometry("540x550")
        self.resizable(False, False)
        self.configure(fg_color=Theme.CONTAINER_BG)

        # Modal window configuration
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (540 // 2)
        y = (self.winfo_screenheight() // 2) - (550 // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text=f"✏️ Edit Device Configuration",
            font=(Theme.FONT_FAMILY, 16, "bold"),
            text_color="#F8FAFC"
        )
        header.pack(pady=(16, 12), padx=20, anchor="w")

        # Parent Device Form Frame
        parent_frame = ctk.CTkFrame(self, fg_color=Theme.PANEL_BG, corner_radius=8)
        parent_frame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            parent_frame,
            text="Device / Branch Name:",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color="#94A3B8"
        ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")

        self.name_entry = ctk.CTkEntry(
            parent_frame,
            width=220,
            height=32
        )
        self.name_entry.insert(0, self.device.name)
        self.name_entry.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        ctk.CTkLabel(
            parent_frame,
            text="IP Address:",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color="#94A3B8"
        ).grid(row=0, column=1, padx=12, pady=(10, 2), sticky="w")

        self.ip_entry = ctk.CTkEntry(
            parent_frame,
            width=220,
            height=32
        )
        self.ip_entry.insert(0, self.device.ip)
        self.ip_entry.grid(row=1, column=1, padx=12, pady=(0, 10), sticky="w")

        # Sub-devices Section Header
        sub_title = ctk.CTkLabel(
            self,
            text="📁 Sub-Devices:",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color="#38BDF8"
        )
        sub_title.pack(padx=20, pady=(4, 6), anchor="w")

        # Scrollable Frame for Sub-devices
        self.sub_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.PANEL_BG,
            height=180,
            corner_radius=8
        )
        self.sub_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.sub_entries = []
        self._render_sub_device_rows()

        # Add Sub-Device inline form
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.new_sub_name = ctk.CTkEntry(
            add_frame,
            placeholder_text="Sub Name (e.g. Switch)",
            width=190,
            height=30
        )
        self.new_sub_name.pack(side="left", padx=(0, 6))

        self.new_sub_ip = ctk.CTkEntry(
            add_frame,
            placeholder_text="Sub IP (e.g. 192.168.1.5)",
            width=190,
            height=30
        )
        self.new_sub_ip.pack(side="left", padx=6)

        ctk.CTkButton(
            add_frame,
            text="➕ Add",
            width=80,
            height=30,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=self._add_new_sub
        ).pack(side="left", padx=(6, 0))

        # Bottom Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 16))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            height=34,
            fg_color="#475569",
            hover_color="#334155",
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            width=130,
            height=34,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            command=self._save_changes
        ).pack(side="right")

    def _render_sub_device_rows(self):
        for child in self.sub_scroll.winfo_children():
            child.destroy()
        self.sub_entries = []

        if not self.device.sub_devices:
            lbl = ctk.CTkLabel(
                self.sub_scroll,
                text="No sub-devices assigned to this branch.",
                font=(Theme.FONT_FAMILY, 11, "italic"),
                text_color="#64748B"
            )
            lbl.pack(pady=10)
            return

        for idx, sub in enumerate(self.device.sub_devices):
            row = ctk.CTkFrame(self.sub_scroll, fg_color=Theme.CONTAINER_BG, corner_radius=6)
            row.pack(fill="x", pady=3, padx=2)

            name_ent = ctk.CTkEntry(row, width=170, height=28)
            name_ent.insert(0, sub.name)
            name_ent.pack(side="left", padx=5, pady=4)

            ip_ent = ctk.CTkEntry(row, width=170, height=28)
            ip_ent.insert(0, sub.ip)
            ip_ent.pack(side="left", padx=5, pady=4)

            del_btn = ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=26,
                fg_color=Theme.ACCENT_RED,
                hover_color=Theme.ACCENT_RED_HOVER,
                command=lambda i=idx: self._delete_sub(i)
            )
            del_btn.pack(side="right", padx=6, pady=4)

            self.sub_entries.append((name_ent, ip_ent))

    def _add_new_sub(self):
        name = self.new_sub_name.get().strip()
        ip = self.new_sub_ip.get().strip()
        if not ip:
            return
        if not name:
            name = ip

        self.device.sub_devices.append(SubDevice(name=name, ip=ip))
        self.new_sub_name.delete(0, "end")
        self.new_sub_ip.delete(0, "end")
        self._render_sub_device_rows()

    def _delete_sub(self, idx: int):
        if 0 <= idx < len(self.device.sub_devices):
            self.device.sub_devices.pop(idx)
            self._render_sub_device_rows()

    def _save_changes(self):
        new_name = self.name_entry.get().strip()
        new_ip = self.ip_entry.get().strip()

        if new_name:
            self.device.name = new_name
        if new_ip:
            self.device.ip = new_ip

        # Update sub-devices from entries
        updated_subs = []
        for name_ent, ip_ent in self.sub_entries:
            s_name = name_ent.get().strip()
            s_ip = ip_ent.get().strip()
            if s_ip:
                updated_subs.append(SubDevice(
                    name=s_name if s_name else s_ip,
                    ip=s_ip
                ))
        self.device.sub_devices = updated_subs

        if self.on_saved:
            self.on_saved(self.device)

        self.destroy()
