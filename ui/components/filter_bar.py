import customtkinter as ctk
from ui.theme import Theme


class FilterBar(ctk.CTkFrame):
    """
    Two-tiered filter & sorting bar:
    Row 1 - Status Filters:
        - All: All devices
        - Offline: Router is Down
        - Online: Router is Up
        - Sub Issues (>=2): Router is Up BUT at least 2 sub-devices are Down
    Row 2 - Branch Type Filters & Dynamic Sorting:
        - All Types: Both Circle K and Franchise
        - Circle K: Branches with Server IP .222
        - Franchise: Branches with Server IP .2
        - Sort: Latest Response (default) vs Alphabetical A-Z
    """

    def __init__(self, master, on_filter_change=None):
        super().__init__(master, fg_color="transparent")
        self.on_filter_change = on_filter_change

        self.active_status_filter = "ALL"       # "ALL", "ONLINE", "OFFLINE", "SUB_ISSUES"
        self.active_type_filter = "ALL"         # "ALL", "CIRCLE_K", "FRANCHISE"
        self.active_sort = "LATEST"             # "LATEST", "NAME"

        # ----------------- ROW 1: STATUS FILTERS -----------------
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(
            row1,
            text="Status:",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color="#94A3B8"
        )
        self.status_lbl.pack(side="left", padx=(0, 6))

        self.all_btn = ctk.CTkButton(
            row1,
            text="All (0)",
            width=70,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=lambda: self._set_status_filter("ALL")
        )
        self.all_btn.pack(side="left", padx=3)

        self.offline_btn = ctk.CTkButton(
            row1,
            text=f"{Theme.DOT_SYMBOL} Offline (0)",
            width=95,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.OFFLINE_BORDER,
            text_color=Theme.OFFLINE_TEXT,
            command=lambda: self._set_status_filter("OFFLINE")
        )
        self.offline_btn.pack(side="left", padx=3)

        self.offline_5m_btn = ctk.CTkButton(
            row1,
            text="⏳ Offline >5m (0)",
            width=125,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#991B1B",
            text_color="#FCA5A5",
            command=lambda: self._set_status_filter("OFFLINE_5M")
        )
        self.offline_5m_btn.pack(side="left", padx=3)

        self.online_btn = ctk.CTkButton(
            row1,
            text=f"{Theme.DOT_SYMBOL} Online (0)",
            width=100,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.ONLINE_BORDER,
            text_color=Theme.ONLINE_TEXT,
            command=lambda: self._set_status_filter("ONLINE")
        )
        self.online_btn.pack(side="left", padx=3)

        self.sub_issues_btn = ctk.CTkButton(
            row1,
            text="⚠️ Sub Issues >=2 (0)",
            width=135,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#B45309",
            text_color="#FBBF24",
            command=lambda: self._set_status_filter("SUB_ISSUES")
        )
        self.sub_issues_btn.pack(side="left", padx=3)

        # ----------------- ROW 2: TYPE FILTERS & SORTING -----------------
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", pady=(2, 0))

        self.type_lbl = ctk.CTkLabel(
            row2,
            text="Type:",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color="#94A3B8"
        )
        self.type_lbl.pack(side="left", padx=(0, 6))

        self.type_all_btn = ctk.CTkButton(
            row2,
            text="All Types (0)",
            width=90,
            height=26,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=lambda: self._set_type_filter("ALL")
        )
        self.type_all_btn.pack(side="left", padx=3)

        self.type_circlek_btn = ctk.CTkButton(
            row2,
            text="🏢 Circle K (0)",
            width=105,
            height=26,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#1E40AF",
            text_color="#93C5FD",
            command=lambda: self._set_type_filter("CIRCLE_K")
        )
        self.type_circlek_btn.pack(side="left", padx=3)

        self.type_franchise_btn = ctk.CTkButton(
            row2,
            text="🤝 Franchise (0)",
            width=110,
            height=26,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#581C87",
            text_color="#D8B4FE",
            command=lambda: self._set_type_filter("FRANCHISE")
        )
        self.type_franchise_btn.pack(side="left", padx=3)

        # Sort Control (Right side of Row 2)
        sort_box = ctk.CTkFrame(row2, fg_color="transparent")
        sort_box.pack(side="right")

        self.sort_lbl = ctk.CTkLabel(
            sort_box,
            text="Sort:",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color="#94A3B8"
        )
        self.sort_lbl.pack(side="left", padx=(0, 6))

        self.sort_latest_btn = ctk.CTkButton(
            sort_box,
            text="🕒 Latest Response",
            width=130,
            height=26,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#0D9488",
            hover_color="#0F766E",
            command=lambda: self._set_sort("LATEST")
        )
        self.sort_latest_btn.pack(side="left", padx=3)

        self.sort_name_btn = ctk.CTkButton(
            sort_box,
            text="🔤 A-Z",
            width=65,
            height=26,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self._set_sort("NAME")
        )
        self.sort_name_btn.pack(side="left", padx=3)

    def _set_status_filter(self, filter_type: str):
        self.active_status_filter = filter_type

        for btn in [self.all_btn, self.offline_btn, self.offline_5m_btn, self.online_btn, self.sub_issues_btn]:
            btn.configure(fg_color="#334155", border_width=0)

        if filter_type == "ALL":
            self.all_btn.configure(fg_color=Theme.ACCENT_BLUE)
        elif filter_type == "OFFLINE":
            self.offline_btn.configure(fg_color=Theme.OFFLINE_BG, border_color=Theme.OFFLINE_BORDER, border_width=1)
        elif filter_type == "OFFLINE_5M":
            self.offline_5m_btn.configure(fg_color="#7F1D1D", border_color="#EF4444", border_width=1)
        elif filter_type == "ONLINE":
            self.online_btn.configure(fg_color=Theme.ONLINE_BG, border_color=Theme.ONLINE_BORDER, border_width=1)
        elif filter_type == "SUB_ISSUES":
            self.sub_issues_btn.configure(fg_color="#451A03", border_color="#D97706", border_width=1)

        self._notify_change()

    def _set_type_filter(self, type_filter: str):
        self.active_type_filter = type_filter

        for btn in [self.type_all_btn, self.type_circlek_btn, self.type_franchise_btn]:
            btn.configure(fg_color="#334155", border_width=0)

        if type_filter == "ALL":
            self.type_all_btn.configure(fg_color=Theme.ACCENT_BLUE)
        elif type_filter == "CIRCLE_K":
            self.type_circlek_btn.configure(fg_color="#1E3A8A", border_color="#3B82F6", border_width=1)
        elif type_filter == "FRANCHISE":
            self.type_franchise_btn.configure(fg_color="#4C1D95", border_color="#8B5CF6", border_width=1)

        self._notify_change()

    def _set_sort(self, sort_type: str):
        self.active_sort = sort_type

        for btn in [self.sort_latest_btn, self.sort_name_btn]:
            btn.configure(fg_color="#334155", border_width=0)

        if sort_type == "LATEST":
            self.sort_latest_btn.configure(fg_color="#0D9488", border_color="#14B8A6", border_width=1)
        elif sort_type == "NAME":
            self.sort_name_btn.configure(fg_color="#0D9488", border_color="#14B8A6", border_width=1)

        self._notify_change()

    def _notify_change(self):
        if self.on_filter_change:
            self.on_filter_change(self.active_status_filter, self.active_type_filter, self.active_sort)

    def update_counts(self, total: int, online: int, offline: int, offline_5m: int = 0, sub_issues: int = 0, circle_k: int = 0, franchise: int = 0):
        self.all_btn.configure(text=f"All ({total})")
        self.offline_btn.configure(text=f"{Theme.DOT_SYMBOL} Offline ({offline})")
        self.offline_5m_btn.configure(text=f"⏳ Offline >5m ({offline_5m})")
        self.online_btn.configure(text=f"{Theme.DOT_SYMBOL} Online ({online})")
        self.sub_issues_btn.configure(text=f"⚠️ Sub Issues >=2 ({sub_issues})")

        self.type_all_btn.configure(text=f"All Types ({total})")
        self.type_circlek_btn.configure(text=f"🏢 Circle K ({circle_k})")
        self.type_franchise_btn.configure(text=f"🤝 Franchise ({franchise})")
