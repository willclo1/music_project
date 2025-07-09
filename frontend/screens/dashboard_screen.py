from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.clock import Clock
import threading, requests

class DashboardScreen(Screen):
    def __init__(self, user_email, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.user_email = user_email
        self.screen_manager = screen_manager
        self.playlist_map = {}

        # ————————————— Gradient Background —————————————
        with self.canvas.before:
            Color(0.02, 0.02, 0.06, 1)
            self.bg_dark = Rectangle(pos=self.pos, size=self.size)
            Color(0.04, 0.04, 0.12, 1)
            self.bg_light = Rectangle(
                pos=(self.x, self.y + self.height * 0.5),
                size=(self.width, self.height * 0.5)
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        # ————————————— Root Layout —————————————
        root = BoxLayout(orientation='vertical', spacing=20, padding=[24, 24, 24, 24])
        self.add_widget(root)

        # ————————————— Header —————————————
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        header.add_widget(Label(
            text="Playlist Dashboard",
            font_size=32, bold=True,
            color=(1, 1, 1, 1),
            size_hint_x=None, width=300
        ))
        header.add_widget(Widget())  # push email to right
        header.add_widget(Label(
            text=self.user_email,
            font_size=16,
            color=(0.7, 0.9, 1, 1),
            size_hint_x=None, width=200
        ))
        root.add_widget(header)

        # ————————————— Tagline & Divider —————————————
        root.add_widget(Label(
            text="Manage your playlists with precision and style.",
            font_size=18, size_hint_y=None, height=30,
            color=(0.85, 0.85, 0.95, 1)
        ))
        root.add_widget(Widget(size_hint_y=None, height=2))

        # ————————————— Main Content (Cards) —————————————
        content = BoxLayout(spacing=30)

        # Create-Playlist Card
        create_card = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with create_card.canvas.before:
            Color(0.10, 0.10, 0.16, 0.9)
            self.create_bg = RoundedRectangle(
                pos=create_card.pos, size=create_card.size, radius=[20]
            )
        create_card.bind(pos=lambda w,p: setattr(self.create_bg,'pos',p),
                         size=lambda w,s: setattr(self.create_bg,'size',s))

        create_card.add_widget(Label(
            text="Create New Playlist", font_size=20,
            color=(1,1,1,1), size_hint_y=None, height=28
        ))
        self.playlist_input = TextInput(
            hint_text="Playlist name",
            size_hint_y=None, height=45,
            background_normal='',
            background_color=(0.08,0.08,0.14,1),
            foreground_color=(1,1,1,1),
            padding=[12,12,12,12]
        )
        create_card.add_widget(self.playlist_input)
        btn_create = Button(
            text="Create Playlist",
            size_hint_y=None, height=45,
            background_normal='',
            background_color=(0.4,0.6,1,1),
            color=(1,1,1,1)
        )
        btn_create.bind(on_press=self.create_playlist)
        create_card.add_widget(btn_create)

        # Select-Playlist Card
        select_card = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with select_card.canvas.before:
            Color(0.10, 0.10, 0.16, 0.9)
            self.select_bg = RoundedRectangle(
                pos=select_card.pos, size=select_card.size, radius=[20]
            )
        select_card.bind(pos=lambda w,p: setattr(self.select_bg,'pos',p),
                         size=lambda w,s: setattr(self.select_bg,'size',s))

        select_card.add_widget(Label(
            text="Select a Playlist", font_size=20,
            color=(1,1,1,1), size_hint_y=None, height=28
        ))
        self.playlist_spinner = Spinner(
            text="Choose…",
            values=[],
            size_hint_y=None, height=45,
            background_normal='',
            background_color=(0.08,0.08,0.14,1),
            color=(1,1,1,1)
        )
        select_card.add_widget(self.playlist_spinner)
        btn_open = Button(
            text="Open Playlist",
            size_hint_y=None, height=45,
            background_normal='',
            background_color=(0.3,0.5,0.9,1),
            color=(1,1,1,1)
        )
        btn_open.bind(on_press=self.open_playlist_detail)
        select_card.add_widget(btn_open)

        content.add_widget(create_card)
        content.add_widget(select_card)
        root.add_widget(content)

        # ————————————— Footer Search Button —————————————
        footer = AnchorLayout(anchor_x='right', anchor_y='bottom',
                              size_hint_y=None, height=80)
        btn_search = Button(
            text="Go to Song Search",
            size_hint=(None,None), size=(220,50),
            background_normal='',
            background_color=(0.2,0.7,0.7,1),
            color=(1,1,1,1)
        )
        btn_search.bind(on_press=self.go_to_search)
        footer.add_widget(btn_search)
        root.add_widget(footer)

        # fetch playlists
        self.populate_playlists()


    def _update_bg(self, *args):
        self.bg_dark.pos = self.pos
        self.bg_dark.size = self.size
        self.bg_light.pos = (self.x, self.y + self.height * 0.5)
        self.bg_light.size = (self.width, self.height * 0.5)

    def populate_playlists(self):
        def _fetch():
            try:
                user_id = requests.get(
                    f"http://127.0.0.1:8000/get_user_id/{self.user_email}"
                ).json().get("user_id")
                data = requests.get(
                    f"http://127.0.0.1:8000/get_playlists/{user_id}"
                ).json().get("playlists", [])
                def ui(dt):
                    self.playlist_map = {p["name"]: p["id"] for p in data}
                    self.playlist_spinner.values = list(self.playlist_map.keys())
                Clock.schedule_once(ui)
            except Exception as e:
                print("Playlist load error:", e)
        threading.Thread(target=_fetch, daemon=True).start()

    def create_playlist(self, *args):
        name = self.playlist_input.text.strip()
        if not name: return
        def _send():
            try:
                res = requests.post(
                    f"http://127.0.0.1:8000/create_playlist/{name}/{self.user_email}"
                ).json()
                pid = res.get("playlist_id")
                self.playlist_map[name] = pid
                Clock.schedule_once(
                    lambda dt: setattr(self.playlist_spinner, 'values',
                                       list(self.playlist_map.keys()))
                )
            except Exception as e:
                print("Create error:", e)
        threading.Thread(target=_send, daemon=True).start()

    def open_playlist_detail(self, *args):
        sel = self.playlist_spinner.text
        pid = self.playlist_map.get(sel)
        if not pid: return
        from frontend.screens.playlist_details_screen import PlaylistDetailScreen
        if not self.screen_manager.has_screen("playlist_detail"):
            self.screen_manager.add_widget(PlaylistDetailScreen(name="playlist_detail"))
        screen = self.screen_manager.get_screen("playlist_detail")
        screen.load_playlist(self.user_email, pid)
        self.screen_manager.current = "playlist_detail"

    def go_to_search(self, *args):
        if not self.screen_manager.has_screen("search"):
            from frontend.screens.search_screen import SearchScreen
            self.screen_manager.add_widget(
                SearchScreen(playlist_map=self.playlist_map,
                             screen_manager=self.screen_manager,
                             name="search")
            )
        else:
            self.screen_manager.get_screen("search").update_playlist_map(self.playlist_map)
        self.screen_manager.current = "search"
