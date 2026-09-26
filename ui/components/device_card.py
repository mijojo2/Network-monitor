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

        # 2. Name & Router IP Stack
        self.name_ip_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.name_ip_frame.grid(row=0, column=2, rowspan=2, sticky="w")

        self.name_lbl = ctk.CTkLabel(
            self.name_ip_frame,
            text=self.device.name,
            font=(Theme.FONT_FAMILY, 15, "bold"),
            anchor="w"
        )
        self.name_lbl.pack(anchor="w")

        self.ip_lbl = ctk.CTkLabel(
            self.name_ip_frame,
            text=f"Router: {self.device.ip}",
            font=(Theme.MONO_FONT, 12, "bold"),
            text_color="#38BDF8",
            anchor="w"
        )
        self.ip_lbl.pack(anchor="w")

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

        sub_inner_header = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        sub_inner_header.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            sub_inner_header,
            text="📁 Sub-Devices (pinged alongside parent branch)",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color="#38BDF8"
        ).pack(side="left")

        self.sub_list_frame = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        self.sub_list_frame.pack(fill="x", padx=10, pady=4)

        # Add Sub-Device inline form
        add_frame = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=(4, 10))

        ctk.CTkLabel(
            add_frame,
            text="Add Sub-Device:",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color="#94A3B8"
        ).pack(side="left", padx=(0, 8))

        self.new_sub_name = ctk.CTkEntry(
            add_frame,
            placeholder_text="Name (e.g. Switch 1)",
            width=160,
            height=28
        )
        self.new_sub_name.pack(side="left", padx=4)
        self.new_sub_name.bind("<Return>", lambda e: self.add_sub_device())

        self.new_sub_ip = ctk.CTkEntry(
            add_frame,
            placeholder_text="IP (e.g. 192.168.1.10)",
            width=150,
            height=28
        )
        self.new_sub_ip.pack(side="left", padx=4)
        self.new_sub_ip.bind("<Return>", lambda e: self.add_sub_device())

        ctk.CTkButton(
            add_frame,
            text="➕ Add",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            width=65,
            height=28,
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
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
        self.render_sub_devices()
        self.sub_container.pack(fill="x", padx=12, pady=(0, 10))
        self.is_expanded = True
        self.update_visual_state(force=True)

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

        # 1. Update Expand Button if count changed or forced
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

        # Update last seen/connected label
        if hasattr(self, "last_seen_lbl"):
            self.last_seen_lbl.configure(text=self.device.get_last_seen_display())
            if status == "Online":
                self.last_seen_lbl.configure(text_color="#94A3B8")
            else:
                self.last_seen_lbl.configure(text_color="#F87171")

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

    def render_sub_devices(self):
        if self.sub_container is None:
            return

        for child in self.sub_list_frame.winfo_children():
            child.destroy()
        self.sub_rows = []

        if not self.device.sub_devices:
            lbl = ctk.CTkLabel(
                self.sub_list_frame,
                text="No sub-devices added yet. Add one below to ping it with this branch.",
                font=(Theme.FONT_FAMILY, 11, "italic"),
                text_color="#64748B"
            )
            lbl.pack(pady=8, anchor="w", padx=10)
            return

        for idx, sub in enumerate(self.device.sub_devices):
            row = ctk.CTkFrame(
                self.sub_list_frame,
                fg_color=Theme.PANEL_BG,
                corner_radius=6,
                height=34
            )
            row.pack(fill="x", pady=2, padx=5)

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

            dot_lbl = ctk.CTkLabel(
                row,
                text=Theme.DOT_SYMBOL,
                font=(Theme.FONT_FAMILY, 16, "bold"),
                text_color=s_color,
                width=24
            )
            dot_lbl.pack(side="left", padx=(8, 4))

            name_lbl = ctk.CTkLabel(
                row,
                text=sub.name,
                font=(Theme.FONT_FAMILY, 12, "bold"),
                text_color="#F1F5F9",
                width=160,
                anchor="w"
            )
            name_lbl.pack(side="left", padx=5)

            ip_lbl = ctk.CTkLabel(
                row,
                text=sub.ip,
                font=(Theme.MONO_FONT, 12),
                text_color="#38BDF8",
                width=140,
                anchor="w"
            )
            ip_lbl.pack(side="left", padx=5)

            status_lbl = ctk.CTkLabel(
                row,
                text=s_text,
                font=(Theme.FONT_FAMILY, 12, "bold"),
                text_color=t_color,
                anchor="w"
            )
            status_lbl.pack(side="left", fill="x", expand=True, padx=10)

            del_btn = ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=24,
                fg_color=Theme.ACCENT_RED,
                hover_color=Theme.ACCENT_RED_HOVER,
                command=lambda i=idx: self.delete_sub_device(i)
            )
            del_btn.pack(side="right", padx=(5, 8))

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
                        row["dot"].configure(text_color=dot_c)
                        row["status"].configure(text=lbl_t, text_color=txt_c)

        state_changed = parent_status_changed or subs_changed
        if state_changed or parent_latency_changed:
            self.update_visual_state(force=False)

        return state_changed
