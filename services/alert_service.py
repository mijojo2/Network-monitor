import time
import threading

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class AlertService:
    """Provides audio and visual alerts when monitored devices go offline."""

    def __init__(self, sound_enabled: bool = True):
        self.sound_enabled = sound_enabled
        self._last_alert_time = 0
        self._alert_cooldown_sec = 2.0  # Cooldown between sounds

    def toggle_sound(self) -> bool:
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled

    def trigger_offline_alert(self, device_name: str, ip: str):
        """Dispatches an audible alert in a background thread if sound is enabled and cooldown passed."""
        if not self.sound_enabled or not WINSOUND_AVAILABLE:
            return

        now = time.time()
        if now - self._last_alert_time < self._alert_cooldown_sec:
            return

        self._last_alert_time = now

        def _play():
            try:
                # Pleasant descending warning tone (600Hz for 150ms then 400Hz for 200ms)
                winsound.Beep(600, 120)
                winsound.Beep(450, 180)
            except Exception:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass

        threading.Thread(target=_play, daemon=True).start()
