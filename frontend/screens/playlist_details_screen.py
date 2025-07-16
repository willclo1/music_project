from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
import requests

def format_duration(ms):
    if ms is not None:
        total_seconds = int(ms) // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    return "0:00"

class PlaylistDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # background
        with self.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # root layout
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        self.add_widget(self.layout)

        # header: back button + title
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=20)
        self.back_btn = Button(
            text="Back",
            size_hint=(None, None),
            size=(100, 40),
            background_color=(0.15, 0.15, 0.2, 1),
            color=(1,1,1,1),
            font_size=14
        )
        self.back_btn.bind(on_release=self.go_to_dashboard)
        header.add_widget(self.back_btn)

        self.title_label = Label(
            text="",
            markup=True,
            font_size=28,
            color=(1,1,1,1),
            halign='left',
            valign='middle'
        )
        header.add_widget(self.title_label)
        header.add_widget(Widget())  # filler to push title left
        self.layout.add_widget(header)

        # subtitle / tagline: song count + total duration
        self.tagline = Label(
            text="",
            font_size=16,
            color=(0.8,0.8,0.9,1),
            size_hint_y=None,
            height=30,
            halign='left',
            valign='middle'
        )
        self.layout.add_widget(self.tagline)

        # scrollable song list container (populated in load_playlist)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.layout.add_widget(self.scroll)

    def load_playlist(self, user_email, playlist_id):
        # fetch playlist name
        if user_email:
            playlist_name = self.get_playlist_name(user_email, playlist_id)
        else:
            playlist_name = self.get_playlist_name_by_id(playlist_id)

        self.title_label.text = f"[b]{playlist_name}[/b]"

        # fetch songs
        songs = self.get_playlist_songs(playlist_id)

        # compute totals
        total_ms = sum(song.get("duration",0) for song in songs)
        self.tagline.text = f"{len(songs)} songs • {format_duration(total_ms)} total"

        # build grid of song cards
        grid = GridLayout(cols=1, spacing=15, padding=[0,10,0,10], size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for idx, song in enumerate(songs, 1):
            card = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=70,
                padding=[15,10],
                spacing=10
            )
            # card background
            with card.canvas.before:
                Color(0.12, 0.12, 0.18, 0.9)
                card.bg = RoundedRectangle(radius=[10], pos=card.pos, size=card.size)
            card.bind(pos=lambda inst, x: setattr(inst.bg, 'pos', inst.pos))
            card.bind(size=lambda inst, x: setattr(inst.bg, 'size', inst.size))

            # song info
            title = song.get("title", "Unknown Title")
            artist = song.get("artist", "Unknown Artist")
            info = Label(
                text=f"[b]{idx}. {title}[/b]\n[i]{artist}[/i]",
                markup=True,
                font_size=16,
                color=(1,1,1,1),
                halign='left',
                valign='middle'
            )
            info.bind(size=info.setter("text_size"))
            card.add_widget(info)

            # duration label
            dur = format_duration(song.get("duration", 0))
            duration = Label(
                text=dur,
                font_size=14,
                color=(0.7,0.7,0.8,1),
                size_hint=(None,1),
                width=80,
                halign='right',
                valign='middle'
            )
            duration.bind(size=duration.setter("text_size"))
            card.add_widget(duration)

            grid.add_widget(card)

        # assign to scroll
        self.scroll.clear_widgets()
        self.scroll.add_widget(grid)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def get_playlist_name(self, email, pid):
        user_id = requests.get(
            f"http://127.0.0.1:8000/get_user_id/{email}"
        ).json().get("user_id")
        playlists = requests.get(
            f"http://127.0.0.1:8000/get_playlists/{user_id}"
        ).json().get("playlists", [])
        return next((p["name"] for p in playlists if p["id"] == pid), "Unknown Playlist")

    def get_playlist_name_by_id(self, pid):
        resp = requests.get(f"http://127.0.0.1:8000/get_playlist_name/{pid}")
        return resp.json().get("name", "Unknown Playlist")

    def get_playlist_songs(self, pid):
        resp = requests.get(f"http://127.0.0.1:8000/get_songs_in_playlist/{pid}")
        return resp.json().get("songs", [])

    def go_to_dashboard(self, *args):
        if self.manager:
            self.manager.current = "dashboard"
