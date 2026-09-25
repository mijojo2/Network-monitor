import customtkinter as ctk
from models import SubDevice


class DeviceCard(ctk.CTkFrame):

    def __init__(self, master, device):
        super().__init__(master, corner_radius=10, fg_color=("#2B2B2B", "#1E293B"))

        self.device = device
        self.selection_callback = None
        self.save_callback = None
        self.is_expanded = False
        self.is_pinging = False
        self.sub_rows = []

        # Ensure sub_devices is a list
        if not hasattr(self.device, "sub_devices") or self.device.sub_devices is None:
            self.device.sub_devices = []

        # Top Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=12, pady=10)

        # 0. Selection Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self.header_frame,
            text="",
            width=24,
            command=self.on_checkbox_changed
        )
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="w")

        # 1. Status Indicator
        self.status = ctk.CTkLabel(
            self.header_frame,
            text="⚪",
            font=("Segoe UI Emoji", 20)
        )
        self.status.grid(row=0, column=1, rowspan=2, padx=(0, 12), sticky="w")

        # 2. Name & IP Frame
        self.name_ip_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.name_ip_frame.grid(row=0, column=2, rowspan=2, sticky="w")

        self.name = ctk.CTkLabel(
            self.name_ip_frame,
            text=device.name,
            font=("Segoe UI", 15, "bold"),
            anchor="w"
        )
        self.name.pack(anchor="w")

        self.ip = ctk.CTkLabel(
            self.name_ip_frame,
            text=device.ip,
            font=("Consolas", 12),
            text_color="#94A3B8",
            anchor="w"
        )
        self.ip.pack(anchor="w")

        self.header_frame.grid_columnconfigure(2, weight=1)

        # 3. Sub-devices Summary Badge
        self.sub_badge = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color="#94A3B8"
        )
        self.sub_badge.grid(row=0, column=3, rowspan=2, padx=10)

        # 4. Latency
        self.latency = ctk.CTkLabel(
            self.header_frame,
            text=device.latency,
            font=("Segoe UI", 13, "bold"),
            text_color="#CBD5E1"
        )
        self.latency.grid(row=0, column=4, rowspan=2, padx=15)

        # 5. Expand / Collapse Sub-devices Button
        self.expand_btn = ctk.CTkButton(
            self.header_frame,
            text=f"▼ Sub-devices ({len(self.device.sub_devices)})",
            font=("Segoe UI", 12),
            width=140,
            height=30,
            fg_color="#334155",
            hover_color="#475569",
            command=self.toggle_expand
        )
        self.expand_btn.grid(row=0, column=5, rowspan=2, padx=(5, 0))

        # Sub-devices Container (initially collapsed)
        self.sub_container = ctk.CTkFrame(
            self,
            fg_color="#0F172A",
            corner_radius=8,
            border_width=1,
            border_color="#334155"
        )

        # Inner header inside sub_container
        self.sub_inner_header = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        self.sub_inner_header.pack(fill="x", padx=10, pady=(8, 4))

        self.sub_title_lbl = ctk.CTkLabel(
            self.sub_inner_header,
            text="📁 Sub-Devices (pinged alongside parent device)",
            font=("Segoe UI", 12, "bold"),
            text_color="#38BDF8"
        )
        self.sub_title_lbl.pack(side="left")

        # Frame holding the list of sub-devices
        self.sub_list_frame = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        self.sub_list_frame.pack(fill="x", padx=10, pady=4)

        # Add Sub-Device row
        self.add_frame = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        self.add_frame.pack(fill="x", padx=10, pady=(4, 10))

        self.add_title_lbl = ctk.CTkLabel(
            self.add_frame,
            text="Add Sub-Device:",
            font=("Segoe UI", 11, "bold"),
            text_color="#94A3B8"
        )
        self.add_title_lbl.pack(side="left", padx=(0, 8))

        self.new_sub_name = ctk.CTkEntry(
            self.add_frame,
            placeholder_text="Name (e.g. Switch 1)",
            width=180,
            height=28
        )
        self.new_sub_name.pack(side="left", padx=4)
        self.new_sub_name.bind("<Return>", lambda e: self.add_sub_device())

        self.new_sub_ip = ctk.CTkEntry(
            self.add_frame,
            placeholder_text="IP (e.g. 192.168.1.10)",
            width=160,
            height=28
        )
        self.new_sub_ip.pack(side="left", padx=4)
        self.new_sub_ip.bind("<Return>", lambda e: self.add_sub_device())

        self.add_btn = ctk.CTkButton(
            self.add_frame,
            text="➕ Add",
            font=("Segoe UI", 12, "bold"),
            width=75,
            height=28,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.add_sub_device
        )
        self.add_btn.pack(side="left", padx=6)

        # Initial render of header badge (sub-devices are rendered on-demand when expanded)
        self.update_header()

    def toggle_expand(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.render_sub_devices()
        self.sub_container.pack(fill="x", padx=12, pady=(0, 10))
        self.is_expanded = True
        self.update_header()

    def collapse(self):
        self.sub_container.pack_forget()
        self.is_expanded = False
        self.update_header()

    def render_sub_devices(self):
        # Clear existing rows
        for child in self.sub_list_frame.winfo_children():
            child.destroy()
        self.sub_rows = []

        if not self.device.sub_devices:
            empty_lbl = ctk.CTkLabel(
                self.sub_list_frame,
                text="No sub-devices added yet. Add one below to ping it with this device.",
                font=("Segoe UI", 11, "italic"),
                text_color="#64748B"
            )
            empty_lbl.pack(pady=8, anchor="w", padx=10)
            return

        for idx, sub in enumerate(self.device.sub_devices):
            row = ctk.CTkFrame(
                self.sub_list_frame,
                fg_color="#1E293B",
                corner_radius=6,
                height=34
            )
            row.pack(fill="x", pady=2, padx=5)

            # Status Icon
            status_text = "⚪"
            if sub.status == "Online":
                status_text = "🟢"
            elif sub.status == "Offline":
                status_text = "🔴"
            elif sub.status == "Checking":
                status_text = "📡"

            status_lbl = ctk.CTkLabel(
                row,
                text=status_text,
                font=("Segoe UI Emoji", 14),
                width=30
            )
            status_lbl.pack(side="left", padx=(8, 4))

            # Sub-device Name
            name_lbl = ctk.CTkLabel(
                row,
                text=sub.name,
                font=("Segoe UI", 12, "bold"),
                text_color="#F1F5F9",
                width=160,
                anchor="w"
            )
            name_lbl.pack(side="left", padx=5)

            # Sub-device IP
            ip_lbl = ctk.CTkLabel(
                row,
                text=sub.ip,
                font=("Consolas", 12),
                text_color="#38BDF8",
                width=140,
                anchor="w"
            )
            ip_lbl.pack(side="left", padx=5)

            # Sub-device Latency
            latency_text = sub.latency
            latency_color = "#94A3B8"
            if sub.status == "Online":
                latency_text = f"Online   {sub.latency}"
                latency_color = "#4ADE80"
            elif sub.status == "Offline":
                latency_text = "Offline"
                latency_color = "#F87171"
            elif sub.status == "Checking":
                latency_text = "Checking..."
                latency_color = "#FBBF24"

            latency_lbl = ctk.CTkLabel(
                row,
                text=latency_text,
                font=("Segoe UI", 12),
                text_color=latency_color,
                anchor="w"
            )
            latency_lbl.pack(side="left", fill="x", expand=True, padx=10)

            # Delete button
            del_btn = ctk.CTkButton(
                row,
                text="✕",
                font=("Arial", 12, "bold"),
                width=28,
                height=24,
                fg_color="#EF4444",
                hover_color="#DC2626",
                command=lambda i=idx: self.delete_sub_device(i)
            )
            del_btn.pack(side="right", padx=(5, 8))

            self.sub_rows.append({
                "status": status_lbl,
                "name": name_lbl,
                "ip": ip_lbl,
                "latency": latency_lbl,
                "delete": del_btn
            })

    def add_sub_device(self):
        name = self.new_sub_name.get().strip()
        ip = self.new_sub_ip.get().strip()

        if not ip:
            self.new_sub_ip.focus_set()
            return

        if not name:
            name = ip

        sub = SubDevice(name=name, ip=ip)
        self.device.sub_devices.append(sub)

        self.new_sub_name.delete(0, "end")
        self.new_sub_ip.delete(0, "end")

        if self.save_callback:
            self.save_callback()

        self.render_sub_devices()
        self.update_header()
        self.new_sub_name.focus_set()

    def delete_sub_device(self, idx):
        if 0 <= idx < len(self.device.sub_devices):
            self.device.sub_devices.pop(idx)

            if self.save_callback:
                self.save_callback()

            self.render_sub_devices()
            self.update_header()

    def update_header(self):
        count = len(self.device.sub_devices)
        arrow = "▲" if self.is_expanded else "▼"
        self.expand_btn.configure(text=f"{arrow} Sub-devices ({count})")

        if count == 0:
            self.sub_badge.configure(text="")
        else:
            online_count = sum(1 for s in self.device.sub_devices if s.status == "Online")
            offline_count = sum(1 for s in self.device.sub_devices if s.status == "Offline")
            checking_count = sum(1 for s in self.device.sub_devices if s.status == "Checking")

            if checking_count > 0:
                self.sub_badge.configure(
                    text=f"📡 Sub: Checking ({count})",
                    text_color="#FBBF24"
                )
            elif online_count == count and count > 0:
                self.sub_badge.configure(
                    text=f"🟢 Sub: {online_count}/{count} Online",
                    text_color="#4ADE80"
                )
            elif offline_count > 0:
                self.sub_badge.configure(
                    text=f"🔴 Sub: {offline_count}/{count} Offline",
                    text_color="#F87171"
                )
            else:
                self.sub_badge.configure(
                    text=f"📌 {count} Sub-devices",
                    text_color="#94A3B8"
                )

    def set_online(self, latency):
        self.status.configure(text="🟢")
        self.latency.configure(text=f"Online   {latency}", text_color="#4ADE80")
        self.device.status = "Online"
        self.device.latency = latency

    def set_offline(self):
        self.status.configure(text="🔴")
        self.latency.configure(text="Offline", text_color="#F87171")
        self.device.status = "Offline"
        self.device.latency = "-"

    def set_checking(self):
        self.status.configure(text="📡")
        self.latency.configure(text="Checking...", text_color="#FBBF24")
        self.device.status = "Checking"

        for idx, sub in enumerate(self.device.sub_devices):
            sub.status = "Checking"
            sub.latency = "Checking..."
            if idx < len(self.sub_rows):
                self.sub_rows[idx]["status"].configure(text="📡")
                self.sub_rows[idx]["latency"].configure(
                    text="Checking...",
                    text_color="#FBBF24"
                )
        self.update_header()

    def update_status(self, online, latency):
        if online:
            self.status.configure(text="🟢")
            self.latency.configure(
                text=f"Online   {latency}",
                text_color="#4ADE80"
            )
            self.device.status = "Online"
            self.device.latency = latency
        else:
            self.status.configure(text="🔴")
            self.latency.configure(
                text="Offline",
                text_color="#F87171"
            )
            self.device.status = "Offline"
            self.device.latency = "-"

    def update_sub_device_status(self, idx, online, latency):
        if 0 <= idx < len(self.device.sub_devices):
            sub = self.device.sub_devices[idx]
            sub.status = "Online" if online else "Offline"
            sub.latency = latency if online else "-"

            if idx < len(self.sub_rows):
                if online:
                    self.sub_rows[idx]["status"].configure(text="🟢")
                    self.sub_rows[idx]["latency"].configure(
                        text=f"Online   {latency}",
                        text_color="#4ADE80"
                    )
                else:
                    self.sub_rows[idx]["status"].configure(text="🔴")
                    self.sub_rows[idx]["latency"].configure(
                        text="Offline",
                        text_color="#F87171"
                    )
            self.update_header()

    def apply_ping_results(self, parent_result, sub_results):
        """Batch update the parent and all sub-devices in a single operation to avoid GUI lag."""
        p_online, p_latency = parent_result
        if p_online:
            self.status.configure(text="🟢")
            self.latency.configure(
                text=f"Online   {p_latency}",
                text_color="#4ADE80"
            )
            self.device.status = "Online"
            self.device.latency = p_latency
        else:
            self.status.configure(text="🔴")
            self.latency.configure(
                text="Offline",
                text_color="#F87171"
            )
            self.device.status = "Offline"
            self.device.latency = "-"

        for idx, (s_online, s_latency) in enumerate(sub_results):
            if idx < len(self.device.sub_devices):
                sub = self.device.sub_devices[idx]
                sub.status = "Online" if s_online else "Offline"
                sub.latency = s_latency if s_online else "-"

                if idx < len(self.sub_rows):
                    row = self.sub_rows[idx]
                    if s_online:
                        row["status"].configure(text="🟢")
                        row["latency"].configure(
                            text=f"Online   {s_latency}",
                            text_color="#4ADE80"
                        )
                    else:
                        row["status"].configure(text="🔴")
                        row["latency"].configure(
                            text="Offline",
                            text_color="#F87171"
                        )

        self.update_header()

    def is_selected(self):
        return self.checkbox.get() == 1

    def set_selected(self, selected: bool):
        if selected:
            self.checkbox.select()
        else:
            self.checkbox.deselect()

    def on_checkbox_changed(self):
        if self.selection_callback:
            self.selection_callback()

