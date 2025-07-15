from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
import threading, requests

class LoginScreen(MDScreen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.user_id = None

        # Gradient-ish background
        with self.canvas.before:
            Color(0.05, 0.06, 0.1, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[0])
        self.bind(pos=self.update_bg, size=self.update_bg)

        # ——— Card Container ———
        card = MDCard(
            orientation="vertical",
            padding=40,
            spacing=25,
            size_hint=(None, None),
            size=(500, 550),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            elevation=15,
            md_bg_color=(0.1, 0.12, 0.2, 0.97),
            radius=[20],
        )
        self.add_widget(card)

        # ——— Title ———
        card.add_widget(MDLabel(
            text="Welcome to Playlist Studio",
            halign="center",
            font_style="H4",
            theme_text_color="Custom",
            text_color=(0.9, 0.95, 1, 1)
        ))

        # ——— Username Field ———
        self.username_input = MDTextField(
            hint_text="Username",
            mode="rectangle",
            size_hint_y=None,
            height=60,
            font_size="18sp",
            text_color_focus=(1, 1, 1, 1)
        )
        card.add_widget(self.username_input)



        # ——— Email Field ———
        self.email_input = MDTextField(
            hint_text="Email",
            mode="rectangle",
            size_hint_y=None,
            height=60,
            font_size="18sp",
            text_color_focus=(1, 1, 1, 1)
        )
        card.add_widget(self.email_input)

        # ——— Status Label ———
        self.status_label = MDLabel(
            text="",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 0.4, 0.4, 1),
            font_style="Caption"
        )
        card.add_widget(self.status_label)

        # ——— Sign-In Button ———
        login_btn = MDRectangleFlatButton(
            text="Sign In or Create Account",
            pos_hint={"center_x": 0.5},
            size_hint=(None, None),
            size=(260, 48),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            line_color=(0.4, 0.7, 1, 1),
        )
        login_btn.bind(on_release=self.authenticate)
        card.add_widget(login_btn)

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

        # Set up the collaboration socket
        try:
            from frontend.client import MySocket
            self.socket = MySocket(host="localhost", port=50000)
            self.socket.request_action(username=email, playlist_id=None, action="WAITING")
            print("Joined collaboration server in WAITING mode.")
        except Exception as e:
            print("Socket setup error:", e)
            self.socket = None  # Fallback so we don't pass garbage

        if self.screen_manager.has_screen("dashboard"):
            self.screen_manager.remove_widget(self.screen_manager.get_screen("dashboard"))

        dashboard_screen = DashboardWrapper(
            user_email=email,
            name="dashboard",
            screen_manager=self.screen_manager,
            socket=self.socket,
        )

        self.screen_manager.add_widget(dashboard_screen)
        self.screen_manager.current = "dashboard"