import customtkinter as ctk
from ui.theme import Theme


class FilterBar(ctk.CTkFrame):
    """Segmented quick-filter bar for device status filtering."""

    def __init__(self, master, on_filter_change=None):
        super().__init__(master, fg_color="transparent")
        self.on_filter_change = on_filter_change
        self.active_filter = "ALL"  # "ALL", "ONLINE", "OFFLINE", "CHECKING"

        # Label
        self.filter_lbl = ctk.CTkLabel(
            self,
            text="Filter:",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color="#94A3B8"
        )
        self.filter_lbl.pack(side="left", padx=(0, 6))

        # All Button
        self.all_btn = ctk.CTkButton(
            self,
            text="All",
            width=65,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=lambda: self._set_filter("ALL")
        )
        self.all_btn.pack(side="left", padx=3)

        # Offline Button
        self.offline_btn = ctk.CTkButton(
            self,
            text=f"{Theme.DOT_SYMBOL} Offline Only",
            width=100,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.OFFLINE_BORDER,
            text_color=Theme.OFFLINE_TEXT,
            command=lambda: self._set_filter("OFFLINE")
        )
        self.offline_btn.pack(side="left", padx=3)

        # Online Button
        self.online_btn = ctk.CTkButton(
            self,
            text=f"{Theme.DOT_SYMBOL} Online Only",
            width=100,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.ONLINE_BORDER,
            text_color=Theme.ONLINE_TEXT,
            command=lambda: self._set_filter("ONLINE")
        )
        self.online_btn.pack(side="left", padx=3)

        # Checking Button
        self.checking_btn = ctk.CTkButton(
            self,
            text=f"{Theme.DOT_SYMBOL} Checking",
            width=85,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color=Theme.CHECKING_BORDER,
            text_color=Theme.CHECKING_TEXT,
            command=lambda: self._set_filter("CHECKING")
        )
        self.checking_btn.pack(side="left", padx=3)

    def _set_filter(self, filter_type: str):
        self.active_filter = filter_type

        # Reset button styles
        for btn in [self.all_btn, self.offline_btn, self.online_btn, self.checking_btn]:
            btn.configure(fg_color="#334155")

        if filter_type == "ALL":
            self.all_btn.configure(fg_color=Theme.ACCENT_BLUE)
        elif filter_type == "OFFLINE":
            self.offline_btn.configure(fg_color=Theme.OFFLINE_BG, border_color=Theme.OFFLINE_BORDER, border_width=1)
        elif filter_type == "ONLINE":
            self.online_btn.configure(fg_color=Theme.ONLINE_BG, border_color=Theme.ONLINE_BORDER, border_width=1)
        elif filter_type == "CHECKING":
            self.checking_btn.configure(fg_color=Theme.CHECKING_BG, border_color=Theme.CHECKING_BORDER, border_width=1)

        if self.on_filter_change:
            self.on_filter_change(self.active_filter)

    def update_counts(self, total: int, online: int, offline: int, checking: int):
        self.all_btn.configure(text=f"All ({total})")
        self.offline_btn.configure(text=f"{Theme.DOT_SYMBOL} Offline ({offline})")
        self.online_btn.configure(text=f"{Theme.DOT_SYMBOL} Online ({online})")
        self.checking_btn.configure(text=f"{Theme.DOT_SYMBOL} Checking ({checking})")
