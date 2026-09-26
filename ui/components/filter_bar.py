import customtkinter as ctk
from ui.theme import Theme


class FilterBar(ctk.CTkFrame):
    """
    Segmented quick-filter bar for device status filtering:
    - All: All devices
    - Offline: Router is Down
    - Online: Router is Up (including partial sub-device issues)
    - Sub Issues (>=2): Router is Up BUT at least 2 sub-devices are Down
    """

    def __init__(self, master, on_filter_change=None):
        super().__init__(master, fg_color="transparent")
        self.on_filter_change = on_filter_change
        self.active_filter = "ALL"  # "ALL", "ONLINE", "OFFLINE", "SUB_ISSUES"

        # Label
        self.filter_lbl = ctk.CTkLabel(
            self,
            text="Filter:",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color="#94A3B8"
        )
        self.filter_lbl.pack(side="left", padx=(0, 6))

        # 1. All Button
        self.all_btn = ctk.CTkButton(
            self,
            text="All (0)",
            width=70,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=lambda: self._set_filter("ALL")
        )
        self.all_btn.pack(side="left", padx=3)

        # 2. Offline Only Button (Router is Down)
        self.offline_btn = ctk.CTkButton(
            self,
            text=f"{Theme.DOT_SYMBOL} Offline (0)",
            width=100,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.OFFLINE_BORDER,
            text_color=Theme.OFFLINE_TEXT,
            command=lambda: self._set_filter("OFFLINE")
        )
        self.offline_btn.pack(side="left", padx=3)

        # 3. Online Only Button (Router is Up, including sub-issues)
        self.online_btn = ctk.CTkButton(
            self,
            text=f"{Theme.DOT_SYMBOL} Online (0)",
            width=100,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.ONLINE_BORDER,
            text_color=Theme.ONLINE_TEXT,
            command=lambda: self._set_filter("ONLINE")
        )
        self.online_btn.pack(side="left", padx=3)

        # 4. Sub Issues Button (Router Online BUT >= 2 Sub-devices Down)
        self.sub_issues_btn = ctk.CTkButton(
            self,
            text="⚠️ Sub Issues >=2 (0)",
            width=135,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#B45309",
            text_color="#FBBF24",
            command=lambda: self._set_filter("SUB_ISSUES")
        )
        self.sub_issues_btn.pack(side="left", padx=3)

    def _set_filter(self, filter_type: str):
        self.active_filter = filter_type

        # Reset button styles
        for btn in [self.all_btn, self.offline_btn, self.online_btn, self.sub_issues_btn]:
            btn.configure(fg_color="#334155", border_width=0)

        if filter_type == "ALL":
            self.all_btn.configure(fg_color=Theme.ACCENT_BLUE)
        elif filter_type == "OFFLINE":
            self.offline_btn.configure(fg_color=Theme.OFFLINE_BG, border_color=Theme.OFFLINE_BORDER, border_width=1)
        elif filter_type == "ONLINE":
            self.online_btn.configure(fg_color=Theme.ONLINE_BG, border_color=Theme.ONLINE_BORDER, border_width=1)
        elif filter_type == "SUB_ISSUES":
            self.sub_issues_btn.configure(fg_color="#451A03", border_color="#D97706", border_width=1)

        if self.on_filter_change:
            self.on_filter_change(self.active_filter)

    def update_counts(self, total: int, online: int, offline: int, sub_issues: int):
        self.all_btn.configure(text=f"All ({total})")
        self.offline_btn.configure(text=f"{Theme.DOT_SYMBOL} Offline ({offline})")
        self.online_btn.configure(text=f"{Theme.DOT_SYMBOL} Online ({online})")
        self.sub_issues_btn.configure(text=f"⚠️ Sub Issues >=2 ({sub_issues})")
