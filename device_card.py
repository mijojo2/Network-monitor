import customtkinter as ctk


class DeviceCard(ctk.CTkFrame):

    def __init__(self, master, device):
        super().__init__(master, corner_radius=10)

        self.device = device

        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            command=self.on_checkbox_changed
        )

        self.selection_callback = None
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=10)

        self.status = ctk.CTkLabel(
            self,
            text="⚪",
            font=("Segoe UI Emoji", 22)
        )
        self.status.grid(row=0, column=1, rowspan=2)

        self.name = ctk.CTkLabel(
            self,
            text=device.name,
            font=("Arial", 16, "bold")
        )
        self.name.grid(row=0, column=2, sticky="w")

        self.ip = ctk.CTkLabel(
            self,
            text=device.ip
        )
        self.ip.grid(row=1, column=2, sticky="w")

        self.latency = ctk.CTkLabel(
            self,
            text=device.latency
        )
        self.latency.grid(row=0, column=3, rowspan=2, padx=20)

        self.grid_columnconfigure(2, weight=1)

    def set_online(self, latency):

        self.status.configure(text="🟢")
        self.latency.configure(text=latency)

    def set_offline(self):

        self.status.configure(text="🔴")
        self.latency.configure(text="Timeout")

    def set_checking(self):

        self.status.configure(text="📡")
        self.latency.configure(
            text="Checking..."
        )

    def update_status(self, online, latency):

        if online:
            self.status.configure(text="🟢")
            self.latency.configure(
                text=f"Online   {latency}"
            )
        else:
            self.status.configure(text="🔴")
            self.latency.configure(
                text="Offline"
            )

    def is_selected(self):
        return self.checkbox.get() == 1

    def on_checkbox_changed(self):

        if self.selection_callback:
            self.selection_callback()
