from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
import threading
import requests


class LoginScreen(BoxLayout):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(orientation='vertical', spacing=30, padding=[60, 80, 60, 80], **kwargs)
        self.screen_manager = screen_manager
        self.user_id = None

        # Background styling
        with self.canvas.before:
            Color(0.08, 0.1, 0.18, 1)  # Deep midnight blue
            self.bg = RoundedRectangle(radius=[12], pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Title
        title = Label(
            text="Welcome to Playlist Studio",
            font_size=36,
            bold=True,
            size_hint_y=None,
            height=70,
            color=(0.9, 0.95, 1, 1)
        )
        self.add_widget(title)

        # Username field
        self.username_input = TextInput(
            hint_text="Username",
            font_size=20,
            multiline=False,
            size_hint_y=None,
            height=60,
            padding=[15, 15],
            background_color=(0.18, 0.18, 0.28, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )
        self.add_widget(self.username_input)

        # Email field
        self.email_input = TextInput(
            hint_text="Email",
            font_size=20,
            multiline=False,
            size_hint_y=None,
            height=60,
            padding=[15, 15],
            background_color=(0.18, 0.18, 0.28, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )
        self.add_widget(self.email_input)

        # Status label
        self.status_label = Label(
            text="",
            font_size=16,
            size_hint_y=None,
            height=40,
            color=(1, 0.4, 0.4, 1)
        )
        self.add_widget(self.status_label)

        # Sign-in button
        login_btn = Button(
            text="Sign In or Create Account",
            size_hint_y=None,
            height=60,
            font_size=20,
            background_color=[0.4, 0.7, 1, 1],
            color=[1, 1, 1, 1]
        )
        login_btn.bind(on_press=self.authenticate)
        self.add_widget(login_btn)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def authenticate(self, instance):
        username = self.username_input.text.strip()
        email = self.email_input.text.strip()

        if not username or not email:
            self.status_label.text = "Please enter both username and email"
            return

        def send_request():
            try:
                url = f"http://127.0.0.1:8000/create_user/{username}/{email}"
                res = requests.post(url)
                if res.status_code == 200:
                    data = res.json()
                    self.user_id = data.get("user_id")
                    msg = data.get("message", "")
                    Clock.schedule_once(lambda dt: self.update_status(f"{msg}"))
                    Clock.schedule_once(lambda dt: self.go_to_dashboard())
                else:
                    Clock.schedule_once(lambda dt: self.update_status("Server error"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)}"))

        threading.Thread(target=send_request, daemon=True).start()

    def update_status(self, msg):
        self.status_label.text = msg

    def go_to_dashboard(self, *args):
        from frontend.main import DashboardWrapper
        email = self.email_input.text.strip()

        if self.screen_manager.has_screen("dashboard"):
            self.screen_manager.remove_widget(self.screen_manager.get_screen("dashboard"))

        dashboard_screen = DashboardWrapper(user_email=email, name="dashboard")
        self.screen_manager.add_widget(dashboard_screen)
        self.screen_manager.current = "dashboard"