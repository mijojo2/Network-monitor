import customtkinter as ctk
from ui.theme import Theme
from core.models import NetworkStats


class StatsBar(ctk.CTkFrame):
    """
    Live monitoring dashboard bar showing:
    Total, Online (X/Total), Offline (Y/Total), Scanning Progress (A/B), Network Health %, and Sound Toggle.
    """

    def __init__(self, master, on_toggle_sound=None):
        super().__init__(
            master,
            fg_color=Theme.PANEL_BG,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=46
        )
        self.on_toggle_sound = on_toggle_sound
        self.sound_enabled = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=0)

        # 1. Total Monitored
        self.total_lbl = ctk.CTkLabel(
            self,
            text="🌐 Total: 0",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color="#F1F5F9"
        )
        self.total_lbl.grid(row=0, column=0, padx=8, pady=8)

        # 2. Online Ratio (e.g. Online: 5/210)
        self.online_lbl = ctk.CTkLabel(
            self,
            text=f"{Theme.DOT_SYMBOL} Online: 0/0",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color=Theme.ONLINE_TEXT
        )
        self.online_lbl.grid(row=0, column=1, padx=8, pady=8)

        # 3. Offline Ratio (e.g. Offline: 145/210)
        self.offline_lbl = ctk.CTkLabel(
            self,
            text=f"{Theme.DOT_SYMBOL} Offline: 0/0",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color=Theme.OFFLINE_TEXT
        )
        self.offline_lbl.grid(row=0, column=2, padx=8, pady=8)

        # 4. Live Scan Cycle Progress (e.g. 📡 Progress: 45/210)
        self.progress_lbl = ctk.CTkLabel(
            self,
            text="📡 Progress: Idle",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color=Theme.CHECKING_TEXT
        )
        self.progress_lbl.grid(row=0, column=3, padx=8, pady=8)

        # 5. Network Stability %
        self.stability_lbl = ctk.CTkLabel(
            self,
            text="⚡ Health: 100%",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color="#38BDF8"
        )
        self.stability_lbl.grid(row=0, column=4, padx=8, pady=8)

        # 6. Sound Alert Toggle
        self.sound_btn = ctk.CTkButton(
            self,
            text="🔔 Sound: ON",
            width=95,
            height=28,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._handle_toggle_sound
        )
        self.sound_btn.grid(row=0, column=5, padx=(5, 12), pady=8)

    def _handle_toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.sound_btn.configure(text="🔔 Sound: ON", fg_color="#334155")
        else:
            self.sound_btn.configure(text="🔕 Sound: OFF", fg_color="#64748B")

        if self.on_toggle_sound:
            self.on_toggle_sound(self.sound_enabled)

    def update_progress(self, current: int, total: int, status_text: str = ""):
        if status_text:
            new_text = status_text
        elif total > 0:
            pct = int((current / total) * 100) if total else 0
            new_text = f"📡 Scanned: {current}/{total} ({pct}%)"
        else:
            new_text = "📡 Progress: Idle"

        if getattr(self, "_last_rendered_progress", None) == new_text:
            return
        self._last_rendered_progress = new_text
        self.progress_lbl.configure(text=new_text)

    def update_stats(self, stats: NetworkStats, total_scope: int = 0):
        scope = total_scope if total_scope > 0 else stats.total_devices
        state = (stats.total_devices, stats.online_devices, stats.offline_devices, stats.stability_percentage, scope)
        if getattr(self, "_last_rendered_stats", None) == state:
            return
        self._last_rendered_stats = state

        self.total_lbl.configure(text=f"🌐 Total: {stats.total_devices}")
        self.online_lbl.configure(text=f"{Theme.DOT_SYMBOL} Online: {stats.online_devices}/{scope}")
        self.offline_lbl.configure(text=f"{Theme.DOT_SYMBOL} Offline: {stats.offline_devices}/{scope}")

        health_color = "#38BDF8"
        if stats.offline_devices > 0:
            health_color = Theme.OFFLINE_TEXT if stats.stability_percentage < 80 else Theme.CHECKING_TEXT
        elif stats.online_devices > 0:
            health_color = Theme.ONLINE_TEXT

        self.stability_lbl.configure(
            text=f"⚡ Health: {stats.stability_percentage}%",
            text_color=health_color
        )
