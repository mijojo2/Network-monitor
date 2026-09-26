import time
import tkinter as tk
import customtkinter as ctk
from core.models import Device, SubDevice
from ui.theme import Theme
from ui.components.edit_dialog import EditDeviceDialog


class DeviceCard(ctk.CTkFrame):
    """
    Card widget representing a single parent device and its sub-devices.
    Includes State-Diffing, lazy sub-container instantiation, Router IP labeling,
    and direct on-header offline sub-device names visibility.
    """

    def __init__(self, master, device: Device, on_delete=None, on_update=None, on_selection_change=None):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=Theme.CARD_BG,
            border_width=1,
            border_color=Theme.BORDER_COLOR
        )

        self.device = device
        self.on_delete = on_delete
        self.on_update = on_update
        self.on_selection_change = on_selection_change

        self.is_expanded = False
        self.sub_rows = []
        self.sub_container = None  # Lazy-initialized to save memory & reduce startup widgets

        # Internal state-diff tracking
        self._rendered_status = None
        self._rendered_latency = None
        self._rendered_sub_state = None

        if not hasattr(self.device, "sub_devices") or self.device.sub_devices is None:
            self.device.sub_devices = []

        self._build_header()
        self.update_visual_state(force=True)

    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=12, pady=10)

        # 0. Selection Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self.header_frame,
            text="",
            width=24,
            command=self._handle_checkbox
        )
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="w")

        # 1. Vibrant Status Dot
        self.status_dot = ctk.CTkLabel(
            self.header_frame,
            text=Theme.DOT_SYMBOL,
            font=(Theme.FONT_FAMILY, 24, "bold"),
            text_color=Theme.UNKNOWN_DOT,
            width=26
        )
        self.status_dot.grid(row=0, column=1, rowspan=2, padx=(0, 10), sticky="w")

        # 2. Name & Router IP Stack (Ultra-lightweight native layout containers)
        self.name_ip_frame = tk.Frame(self.header_frame, bg=Theme.CARD_BG)
        self.name_ip_frame.grid(row=0, column=2, rowspan=2, sticky="w")

        name_row = tk.Frame(self.name_ip_frame, bg=Theme.CARD_BG)
        name_row.pack(anchor="w")

        self.name_lbl = ctk.CTkLabel(
            name_row,
            text=self.device.name,
            font=(Theme.FONT_FAMILY, 15, "bold"),
            anchor="w"
        )
        self.name_lbl.pack(side="left")

        b_type = self.device.get_branch_type()
        if b_type == "CircleK":
            self.type_badge = ctk.CTkLabel(
                name_row,
                text="🏢 Circle K",
                font=(Theme.FONT_FAMILY, 10, "bold"),
                text_color="#60A5FA",
                fg_color="#1E293B",
                corner_radius=4,
                padx=6,
                pady=1
            )
            self.type_badge.pack(side="left", padx=(8, 0))
        elif b_type == "Franchise":
            self.type_badge = ctk.CTkLabel(
                name_row,
                text="🤝 Franchise",
                font=(Theme.FONT_FAMILY, 10, "bold"),
                text_color="#C084FC",
                fg_color="#2E1065",
                corner_radius=4,
                padx=6,
                pady=1
            )
            self.type_badge.pack(side="left", padx=(8, 0))

        # Visual Outage Alert Bell Badge (Shown when branch drops)
        self.alert_badge = ctk.CTkLabel(
            name_row,
            text="🔔 Outage Alert",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color="#FCA5A5",
            fg_color="#7F1D1D",
            corner_radius=4,
            padx=6,
            pady=1
        )
        self.has_active_alert = False

        # IPs row: Router IP + Dedicated Server Status Badge
        self.ips_row = tk.Frame(self.name_ip_frame, bg=Theme.CARD_BG)
        self.ips_row.pack(anchor="w", pady=(2, 0))

        self.ip_lbl = ctk.CTkLabel(
            self.ips_row,
            text=f"Router: {self.device.ip}",
            font=(Theme.MONO_FONT, 12, "bold"),
            text_color="#38BDF8",
            anchor="w"
        )
        self.ip_lbl.pack(side="left")

        self.server_badge = ctk.CTkButton(
            self.ips_row,
            text="🖥️ Server: N/A",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            height=22,
            corner_radius=5,
            cursor="hand2",
            command=self._copy_server_ip
        )
        self.server_badge.pack(side="left", padx=(10, 0))

        self.last_seen_lbl = ctk.CTkLabel(
            self.name_ip_frame,
            text=self.device.get_last_seen_display(),
            font=(Theme.FONT_FAMILY, 10),
            text_color="#94A3B8",
            anchor="w"
        )
        self.last_seen_lbl.pack(anchor="w", pady=(1, 0))

        self.header_frame.grid_columnconfigure(2, weight=1)

        # 3. Sub-devices Summary Pill (Shows exact offline machine names from outside)
        self.sub_badge = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color="#94A3B8"
        )
        self.sub_badge.grid(row=0, column=3, rowspan=2, padx=12)

        # 4. Status Pill Badge (Vibrant Container)
        self.status_pill = ctk.CTkFrame(
            self.header_frame,
            corner_radius=12,
            fg_color=Theme.UNKNOWN_BG,
            border_width=1,
            border_color=Theme.UNKNOWN_BORDER,
            height=28
        )
        self.status_pill.grid(row=0, column=4, rowspan=2, padx=10)

        self.pill_lbl = ctk.CTkLabel(
            self.status_pill,
            text=f"{Theme.DOT_SYMBOL} Unknown",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color=Theme.UNKNOWN_TEXT,
            padx=12,
            pady=3
        )
        self.pill_lbl.pack()

        # 5. Edit Button
        self.edit_btn = ctk.CTkButton(
            self.header_frame,
            text="✏️ Edit",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            width=65,
            height=30,
            fg_color="#334155",
            hover_color="#475569",
            command=self._open_edit_dialog
        )
        self.edit_btn.grid(row=0, column=5, rowspan=2, padx=4)

        # 6. Expand / Collapse Sub-devices Button
        self.expand_btn = ctk.CTkButton(
            self.header_frame,
            text=f"▼ Sub-devices ({len(self.device.sub_devices)})",
            font=(Theme.FONT_FAMILY, 12),
            width=140,
            height=30,
            fg_color="#334155",
            hover_color="#475569",
            command=self.toggle_expand
        )
        self.expand_btn.grid(row=0, column=6, rowspan=2, padx=(4, 0))

    def _build_sub_container(self):
        """Constructs sub-devices accordion frame only on demand (lazy loading)."""
        self.sub_container = ctk.CTkFrame(
            self,
            fg_color=Theme.CONTAINER_BG,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_COLOR
        )

        sub_inner_header = tk.Frame(self.sub_container, bg=Theme.CONTAINER_BG)
        sub_inner_header.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(
            sub_inner_header,
            text="📁 Sub-Devices (pinged alongside parent branch)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg="#38BDF8",
            bg=Theme.CONTAINER_BG
        ).pack(side="left")

        self.sub_list_frame = tk.Frame(self.sub_container, bg=Theme.CONTAINER_BG)
        self.sub_list_frame.pack(fill="x", padx=8, pady=2)

        # Add Sub-Device inline form
        add_frame = tk.Frame(self.sub_container, bg=Theme.CONTAINER_BG)
        add_frame.pack(fill="x", padx=8, pady=(4, 8))

        tk.Label(
            add_frame,
            text="Add Sub-Device:",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            fg="#94A3B8",
            bg=Theme.CONTAINER_BG
        ).pack(side="left", padx=(0, 6))

        self.new_sub_name = tk.Entry(
            add_frame,
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.PANEL_BG,
            fg="#F1F5F9",
            insertbackground="white",
            bd=1,
            relief="solid",
            width=16
        )
        self.new_sub_name.pack(side="left", padx=4)
        self.new_sub_name.bind("<Return>", lambda e: self.add_sub_device())

        self.new_sub_ip = tk.Entry(
            add_frame,
            font=(Theme.MONO_FONT, 10),
            bg=Theme.PANEL_BG,
            fg="#38BDF8",
            insertbackground="white",
            bd=1,
            relief="solid",
            width=16
        )
        self.new_sub_ip.pack(side="left", padx=4)
        self.new_sub_ip.bind("<Return>", lambda e: self.add_sub_device())

        tk.Button(
            add_frame,
            text="➕ Add",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            bg=Theme.ACCENT_BLUE,
            fg="white",
            activebackground=Theme.ACCENT_BLUE_HOVER,
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.add_sub_device
        ).pack(side="left", padx=6)

    def _open_edit_dialog(self):
        def _on_edited(dev):
            self.name_lbl.configure(text=dev.name)
            self.ip_lbl.configure(text=f"Router: {dev.ip}")
            self.update_visual_state(force=True)
            if self.is_expanded and self.sub_container is not None:
                self.render_sub_devices()
            if self.on_update:
                self.on_update()

        EditDeviceDialog(self.winfo_toplevel(), self.device, on_saved=_on_edited)

    def _handle_checkbox(self):
        if self.on_selection_change:
            self.on_selection_change()

    def is_selected(self) -> bool:
        return self.checkbox.get() == 1

    def set_selected(self, selected: bool):
        if selected:
            self.checkbox.select()
        else:
            self.checkbox.deselect()

    def toggle_expand(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        if self.sub_container is None:
            self._build_sub_container()
        if not self.sub_rows:
            self.render_sub_devices()
        if not self.sub_container.winfo_ismapped():
            self.sub_container.pack(fill="x", padx=12, pady=(0, 10))
        self.is_expanded = True
        self.update_visual_state(force=False)

    def collapse(self):
        if self.sub_container is not None:
            self.sub_container.pack_forget()
        self.is_expanded = False
        self.update_visual_state(force=True)

    def update_visual_state(self, force: bool = False):
        """
        Applies UI updates conditionally using State-Diffing.
        Displays exact offline sub-device names directly on the card header.
        """
        status = self.device.status
        latency = self.device.latency
        count = len(self.device.sub_devices)

        # 1. Update Expand Button if count/state changed or forced
        expand_state = (self.is_expanded, count)
        if getattr(self, "_rendered_expand_state", None) != expand_state or force:
            self._rendered_expand_state = expand_state
            arrow = "▲" if self.is_expanded else "▼"
            self.expand_btn.configure(text=f"{arrow} Sub-devices ({count})")

        # 2. Check if Parent Status or Latency changed
        status_changed = (status != self._rendered_status) or force
        latency_changed = (latency != self._rendered_latency)

        if status_changed:
            self._rendered_status = status
            self._rendered_latency = latency

            if status == "Online":
                self.status_dot.configure(text=Theme.DOT_SYMBOL, text_color=Theme.ONLINE_DOT)
                self.status_pill.configure(fg_color=Theme.ONLINE_BG, border_color=Theme.ONLINE_BORDER)
                self.pill_lbl.configure(text=f"{Theme.DOT_SYMBOL} Online   {latency}", text_color=Theme.ONLINE_TEXT)
                self.configure(border_color=Theme.ONLINE_BORDER)

            elif status == "Offline":
                self.status_dot.configure(text=Theme.DOT_SYMBOL, text_color=Theme.OFFLINE_DOT)
                self.status_pill.configure(fg_color=Theme.OFFLINE_BG, border_color=Theme.OFFLINE_BORDER)
                self.pill_lbl.configure(text=f"{Theme.DOT_SYMBOL} Offline", text_color=Theme.OFFLINE_TEXT)
                self.configure(border_color=Theme.OFFLINE_BORDER)

            elif status == "Checking":
                self.status_dot.configure(text=Theme.DOT_SYMBOL, text_color=Theme.CHECKING_DOT)
                self.status_pill.configure(fg_color=Theme.CHECKING_BG, border_color=Theme.CHECKING_BORDER)
                self.pill_lbl.configure(text=f"{Theme.DOT_SYMBOL} Checking...", text_color=Theme.CHECKING_TEXT)
                self.configure(border_color=Theme.CHECKING_BORDER)

            else:
                self.status_dot.configure(text=Theme.DOT_SYMBOL, text_color=Theme.UNKNOWN_DOT)
                self.status_pill.configure(fg_color=Theme.UNKNOWN_BG, border_color=Theme.UNKNOWN_BORDER)
                self.pill_lbl.configure(text=f"{Theme.DOT_SYMBOL} Unknown", text_color=Theme.UNKNOWN_TEXT)
                self.configure(border_color=Theme.BORDER_COLOR)

        elif latency_changed and status == "Online":
            self._rendered_latency = latency
            self.pill_lbl.configure(text=f"{Theme.DOT_SYMBOL} Online   {latency}")

        # Update last seen/connected label with live State-Diffing
        self.refresh_last_seen_display()
        if status == "Online" and getattr(self, "has_active_alert", False):
            self.set_alert_state(False)

        # 3. Sub-devices Summary & Direct Offline Names Visibility
        offline_subs = [s.name for s in self.device.sub_devices if s.status == "Offline"]
        online_subs = [s.name for s in self.device.sub_devices if s.status == "Online"]
        checking_subs = [s.name for s in self.device.sub_devices if s.status == "Checking"]
        current_sub_state = (tuple(offline_subs), tuple(online_subs), tuple(checking_subs))

        if current_sub_state != self._rendered_sub_state or force:
            self._rendered_sub_state = current_sub_state

            if count == 0:
                self.sub_badge.configure(text="")
            else:
                if offline_subs:
                    # Show EXACT offline sub-device names directly on the card header!
                    offline_count = len(offline_subs)
                    if offline_count == count:
                        names_joined = ", ".join(offline_subs)
                        self.sub_badge.configure(
                            text=f"{Theme.DOT_SYMBOL} All Sub Down ({names_joined})",
                            text_color=Theme.OFFLINE_TEXT
                        )
                    else:
                        names_joined = ", ".join(offline_subs)
                        self.sub_badge.configure(
                            text=f"{Theme.DOT_SYMBOL} Down: {names_joined}",
                            text_color=Theme.OFFLINE_TEXT
                        )
                elif checking_subs:
                    self.sub_badge.configure(
                        text=f"{Theme.DOT_SYMBOL} Sub: Checking ({len(checking_subs)})",
                        text_color=Theme.CHECKING_TEXT
                    )
                elif len(online_subs) == count and count > 0:
                    self.sub_badge.configure(
                        text=f"{Theme.DOT_SYMBOL} All Sub Online ({count}/{count})",
                        text_color=Theme.ONLINE_TEXT
                    )
                else:
                    self.sub_badge.configure(
                        text=f"📌 {count} Sub-devices",
                        text_color="#94A3B8"
                    )

        # 4. Direct Server Status & IP Visibility on Header
        self._update_server_badge(force=force)

    def _update_server_badge(self, force: bool = False):
        """
        Updates the header Server badge with live IP, status, and latency.
        Critically highlights the deceptive failure where Router is Online but Server is Offline.
        """
        if not hasattr(self, "server_badge"):
            return

        server_sub = self.device.get_server_sub_device()
        if not server_sub:
            if self.server_badge.winfo_ismapped():
                self.server_badge.pack_forget()
            return

        if not self.server_badge.winfo_ismapped():
            self.server_badge.pack(side="left", padx=(10, 0))

        s_ip = server_sub.ip
        s_status = server_sub.status
        s_latency = server_sub.latency
        router_status = self.device.status

        current_server_state = (s_ip, s_status, s_latency, router_status)
        if getattr(self, "_rendered_server_state", None) == current_server_state and not force:
            return
        self._rendered_server_state = current_server_state

        if s_status == "Online":
            lat_str = f" ({s_latency})" if s_latency and s_latency != "-" else ""
            self.server_badge.configure(
                text=f"🖥️ Server: {s_ip}  ● Online{lat_str}",
                fg_color="#064E3B",
                text_color="#6EE7B7",
                border_color="#059669",
                border_width=1,
                hover_color="#047857"
            )
        elif s_status == "Offline":
            if router_status == "Online":
                # THE DECEPTIVE OUTAGE: Router is UP, but internal Server is DEAD!
                self.server_badge.configure(
                    text=f"⚠️ SERVER OFFLINE: {s_ip}",
                    fg_color="#7F1D1D",
                    text_color="#FCA5A5",
                    border_color="#EF4444",
                    border_width=1.5,
                    hover_color="#991B1B"
                )
            else:
                self.server_badge.configure(
                    text=f"🖥️ Server: {s_ip}  ● Offline",
                    fg_color="#1E293B",
                    text_color="#94A3B8",
                    border_color="#475569",
                    border_width=1,
                    hover_color="#334155"
                )
        elif s_status == "Checking":
            self.server_badge.configure(
                text=f"🖥️ Server: {s_ip}  ● Checking...",
                fg_color="#1E293B",
                text_color="#93C5FD",
                border_color="#3B82F6",
                border_width=1,
                hover_color="#1E3A8A"
            )
        else:
            self.server_badge.configure(
                text=f"🖥️ Server: {s_ip}  ● Unknown",
                fg_color="#1E293B",
                text_color="#94A3B8",
                border_color="#334155",
                border_width=1,
                hover_color="#334155"
            )

    def _copy_server_ip(self):
        """Copies the Server IP to system clipboard with instant tactile feedback."""
        server_sub = self.device.get_server_sub_device()
        if not server_sub or not server_sub.ip:
            return
        ip = server_sub.ip
        try:
            self.clipboard_clear()
            self.clipboard_append(ip)
            self.server_badge.configure(text=f"📋 Copied {ip}!")
            self.after(1200, self._update_server_badge)
        except Exception:
            pass

    def refresh_last_seen_display(self):
        """
        Refreshes the last_seen_lbl with live minute progression (e.g. <1 min, 1 min, 2 min, 5 min).
        Uses State-Diffing to avoid touching Tkinter widgets unless text actually changed.
        """
        if hasattr(self, "last_seen_lbl"):
            new_text = self.device.get_last_seen_display()
            if self.last_seen_lbl.cget("text") != new_text:
                self.last_seen_lbl.configure(text=new_text)
                if self.device.status == "Online":
                    self.last_seen_lbl.configure(text_color="#94A3B8")
                else:
                    self.last_seen_lbl.configure(text_color="#F87171")

    def render_sub_devices(self):
        if self.sub_container is None:
            return

        for child in self.sub_list_frame.winfo_children():
            child.destroy()
        self.sub_rows = []

        if not self.device.sub_devices:
            lbl = tk.Label(
                self.sub_list_frame,
                text="No sub-devices added yet. Add one below to ping it with this branch.",
                font=(Theme.FONT_FAMILY, 10, "italic"),
                fg="#64748B",
                bg=Theme.CONTAINER_BG
            )
            lbl.pack(pady=6, anchor="w", padx=8)
            return

        for idx, sub in enumerate(self.device.sub_devices):
            row = tk.Frame(
                self.sub_list_frame,
                bg=Theme.PANEL_BG,
                padx=8,
                pady=3
            )
            row.pack(fill="x", pady=1, padx=2)

            s_color = Theme.UNKNOWN_DOT
            s_text = f"{Theme.DOT_SYMBOL} Unknown"
            t_color = Theme.UNKNOWN_TEXT

            if sub.status == "Online":
                s_color = Theme.ONLINE_DOT
                s_text = f"{Theme.DOT_SYMBOL} Online   {sub.latency}"
                t_color = Theme.ONLINE_TEXT
            elif sub.status == "Offline":
                s_color = Theme.OFFLINE_DOT
                s_text = f"{Theme.DOT_SYMBOL} Offline"
                t_color = Theme.OFFLINE_TEXT
            elif sub.status == "Checking":
                s_color = Theme.CHECKING_DOT
                s_text = f"{Theme.DOT_SYMBOL} Checking..."
                t_color = Theme.CHECKING_TEXT

            dot_lbl = tk.Label(
                row,
                text=Theme.DOT_SYMBOL,
                font=(Theme.FONT_FAMILY, 14, "bold"),
                fg=s_color,
                bg=Theme.PANEL_BG,
                width=2
            )
            dot_lbl.pack(side="left", padx=(0, 4))

            name_lbl = tk.Label(
                row,
                text=sub.name,
                font=(Theme.FONT_FAMILY, 11, "bold"),
                fg="#F1F5F9",
                bg=Theme.PANEL_BG,
                width=18,
                anchor="w"
            )
            name_lbl.pack(side="left", padx=4)

            ip_lbl = tk.Label(
                row,
                text=sub.ip,
                font=(Theme.MONO_FONT, 11),
                fg="#38BDF8",
                bg=Theme.PANEL_BG,
                width=16,
                anchor="w"
            )
            ip_lbl.pack(side="left", padx=4)

            status_lbl = tk.Label(
                row,
                text=s_text,
                font=(Theme.FONT_FAMILY, 11, "bold"),
                fg=t_color,
                bg=Theme.PANEL_BG,
                anchor="w"
            )
            status_lbl.pack(side="left", fill="x", expand=True, padx=8)

            del_btn = tk.Button(
                row,
                text="✕",
                font=(Theme.FONT_FAMILY, 9, "bold"),
                bg="#EF4444",
                fg="white",
                activebackground="#DC2626",
                activeforeground="white",
                bd=0,
                relief="flat",
                padx=6,
                pady=0,
                cursor="hand2",
                command=lambda i=idx: self.delete_sub_device(i)
            )
            del_btn.pack(side="right", padx=(4, 0))

            self.sub_rows.append({
                "dot": dot_lbl,
                "name": name_lbl,
                "ip": ip_lbl,
                "status": status_lbl,
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

        self.device.sub_devices.append(SubDevice(name=name, ip=ip))
        self.new_sub_name.delete(0, "end")
        self.new_sub_ip.delete(0, "end")

        if self.on_update:
            self.on_update()

        self.render_sub_devices()
        self.update_visual_state(force=True)

    def delete_sub_device(self, idx: int):
        if 0 <= idx < len(self.device.sub_devices):
            self.device.sub_devices.pop(idx)
            if self.on_update:
                self.on_update()
            self.render_sub_devices()
            self.update_visual_state(force=True)

    def set_checking(self):
        self.device.status = "Checking"
        for sub in self.device.sub_devices:
            sub.status = "Checking"
            sub.latency = "Checking..."
        self.update_visual_state()
        if self.is_expanded and self.sub_container is not None:
            for row in self.sub_rows:
                try:
                    row["dot"].configure(fg=Theme.CHECKING_DOT)
                    row["status"].configure(text=f"{Theme.DOT_SYMBOL} Checking...", fg=Theme.CHECKING_TEXT)
                except Exception:
                    row["dot"].configure(text_color=Theme.CHECKING_DOT)
                    row["status"].configure(text=f"{Theme.DOT_SYMBOL} Checking...", text_color=Theme.CHECKING_TEXT)

    def apply_ping_results(self, parent_result, sub_results) -> bool:
        """
        Applies ping results with State-Diffing.
        Only updates widgets if state or sub-device status actually changed.
        """
        p_online, p_latency = parent_result
        now = time.time()
        self.device.last_check = now
        if p_online:
            self.device.last_seen = now
            self.device.offline_since = None
        else:
            if getattr(self.device, "offline_since", None) is None:
                self.device.offline_since = self.device.last_seen or now

        new_status = "Online" if p_online else "Offline"
        new_latency = p_latency if p_online else "-"

        parent_status_changed = (new_status != self.device.status)
        parent_latency_changed = (new_status == "Online" and new_latency != self.device.latency)

        self.device.status = new_status
        self.device.latency = new_latency

        subs_changed = False
        for idx, (s_online, s_latency) in enumerate(sub_results):
            if idx < len(self.device.sub_devices):
                sub = self.device.sub_devices[idx]
                s_new_status = "Online" if s_online else "Offline"
                s_new_latency = s_latency if s_online else "-"

                if s_new_status != sub.status or (s_new_status == "Online" and s_new_latency != sub.latency):
                    subs_changed = True
                    sub.status = s_new_status
                    sub.latency = s_new_latency

                    # Targeted sub-row repaint only if expanded and rendered
                    if self.is_expanded and idx < len(self.sub_rows):
                        row = self.sub_rows[idx]
                        dot_c = Theme.ONLINE_DOT if s_online else Theme.OFFLINE_DOT
                        txt_c = Theme.ONLINE_TEXT if s_online else Theme.OFFLINE_TEXT
                        lbl_t = f"{Theme.DOT_SYMBOL} Online   {s_latency}" if s_online else f"{Theme.DOT_SYMBOL} Offline"
                        try:
                            row["dot"].configure(fg=dot_c)
                            row["status"].configure(text=lbl_t, fg=txt_c)
                        except Exception:
                            row["dot"].configure(text_color=dot_c)
                            row["status"].configure(text=lbl_t, text_color=txt_c)

        state_changed = parent_status_changed or subs_changed
        if state_changed or parent_latency_changed:
            self.update_visual_state(force=False)
        else:
            self.refresh_last_seen_display()

        return state_changed

    def set_alert_state(self, is_alert: bool):
        """Displays or hides the visual bell alert badge when a branch drops."""
        self.has_active_alert = is_alert
        if is_alert:
            if not self.alert_badge.winfo_ismapped():
                self.alert_badge.pack(side="left", padx=(8, 0))
        else:
            if self.alert_badge.winfo_ismapped():
                self.alert_badge.pack_forget()
