from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
import requests

from frontend.screens.playlist_details_screen import format_duration


class CollabEditScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.playlist_id = None
        self.user_email = None
        self.socket = None

        with self.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        self.add_widget(self.layout)

        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=20)
        self.back_btn = Button(text="Back", size_hint=(None, None), size=(100, 40))
        self.back_btn.bind(on_release=self.go_to_dashboard)
        header.add_widget(self.back_btn)

        self.title_label = Label(text="", font_size=28, color=(1,1,1,1))
        header.add_widget(self.title_label)
        header.add_widget(Label())  # Spacer
        self.layout.add_widget(header)

        # Add song input
        add_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.song_input = TextInput(hint_text="Enter song title", multiline=False)
        self.add_btn = Button(text="Add Song")
        self.add_btn.bind(on_release=self.add_song)
        add_box.add_widget(self.song_input)
        add_box.add_widget(self.add_btn)
        self.layout.add_widget(add_box)

        # Tagline
        self.tagline = Label(text="", font_size=16, color=(0.8,0.8,0.9,1), size_hint_y=None, height=30)
        self.layout.add_widget(self.tagline)

        # Scrollable song list
        self.scroll = ScrollView()
        self.layout.add_widget(self.scroll)

    def load_collab_session(self, user_email, playlist_id, socket):
        self.user_email = user_email
        self.playlist_id = playlist_id
        self.socket = socket
        self.refresh_playlist()
        self.setup_websocket()

    def refresh_playlist(self):
        songs = self.get_playlist_songs(self.playlist_id)
        total_ms = sum(song.get("duration", 0) for song in songs)
        self.tagline.text = f"{len(songs)} songs • {format_duration(total_ms)} total"

        grid = GridLayout(cols=1, spacing=15, padding=[0,10,0,10], size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for idx, song in enumerate(songs, 1):
            card = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10)
            with card.canvas.before:
                Color(0.12, 0.12, 0.18, 0.9)
                card.bg = RoundedRectangle(radius=[10], pos=card.pos, size=card.size)
            card.bind(pos=lambda inst, x: setattr(inst.bg, 'pos', inst.pos))
            card.bind(size=lambda inst, x: setattr(inst.bg, 'size', inst.size))

            info = Label(text=f"[b]{idx}. {song['title']}[/b]\n[i]{song['artist']}[/i]",
                         markup=True, font_size=16, color=(1,1,1,1))
            info.bind(size=info.setter("text_size"))
            card.add_widget(info)

            remove_btn = Button(text="Remove", size_hint=(None, 1), width=100)
            remove_btn.bind(on_release=lambda btn, s=song: self.remove_song(s))
            card.add_widget(remove_btn)

            grid.add_widget(card)

        self.scroll.clear_widgets()
        self.scroll.add_widget(grid)

    def add_song(self, *args):
        title = self.song_input.text.strip()
        if not title:
            return
        self.socket.request_action(
            username=self.user_email,
            playlist_id=self.playlist_id,
            action="ADD_SONG",
            song_data={"title": title}
        )
        self.song_input.text = ""

    def remove_song(self, song):
        self.socket.request_action(
            username=self.user_email,
            playlist_id=self.playlist_id,
            action="REMOVE_SONG",
            song_data=song
        )

    def setup_websocket(self):
        # Subscribe to playlist updates
        self.socket.subscribe_to_playlist(self.playlist_id, self.on_playlist_update)

    def on_playlist_update(self, update_data):
        Clock.schedule_once(lambda dt: self.refresh_playlist())

    def get_playlist_songs(self, pid):
        resp = requests.get(f"http://127.0.0.1:8000/get_songs_in_playlist/{pid}")
        return resp.json().get("songs", [])

    def go_to_dashboard(self, *args):
        if self.manager:
            self.manager.current = "dashboard"

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
