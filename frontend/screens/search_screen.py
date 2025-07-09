from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
import threading, requests, urllib.parse

class SearchScreen(Screen):
    def __init__(self, playlist_map, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.playlist_map = playlist_map
        self.screen_manager = screen_manager

        # ————— Gradient Background —————
        with self.canvas.before:
            Color(0.02, 0.02, 0.06, 1)
            self.bg_dark = Rectangle(pos=self.pos, size=self.size)
            Color(0.04, 0.04, 0.12, 1)
            self.bg_light = Rectangle(
                pos=(self.x, self.y + self.height * 0.6),
                size=(self.width, self.height * 0.4)
            )
        self.bind(size=self._update_bg, pos=self._update_bg)

        # ————— Root Layout —————
        root = BoxLayout(orientation='vertical', spacing=20, padding=30)
        self.add_widget(root)

        # ————— Header —————
        header = BoxLayout(size_hint_y=None, height=60)
        header.add_widget(Label(
            text="Song Search", font_size=32, bold=True, color=(1,1,1,1),
            size_hint_x=None, width=250
        ))

        header.add_widget(Widget())  # spacer
        header.add_widget(Label(
            text="Add to playlist", font_size=18, italic=True, color=(0.7,0.9,1,1),
            size_hint_x=None, width=250
        ))
        root.add_widget(header)

        # ————— Tagline —————
        root.add_widget(Label(
            text="Search MusicBrainz and add recordings to your playlist",
            font_size=16, color=(0.85,0.85,0.95,1),
            size_hint_y=None, height=30
        ))

        # ————— Proper Divider —————
        divider = Widget(size_hint_y=None, height=2)
        with divider.canvas.before:
            Color(0.5, 0.5, 0.6, 1)
            self._div_rect = Rectangle(pos=divider.pos, size=divider.size)
        # keep the rectangle in sync with the widget
        divider.bind(pos=lambda w, p: setattr(self._div_rect, 'pos', p),
                     size=lambda w, s: setattr(self._div_rect, 'size', s))
        root.add_widget(divider)

        # ————— Playlist Selector —————
        self.playlist_btn = Button(
            text="Select Playlist…",
            size_hint_y=None, height=50,
            background_normal='', background_color=(0.08,0.08,0.14,1),
            color=(1,1,1,1), font_size=16
        )
        self.playlist_btn.bind(on_press=self.open_playlist_popup)
        root.add_widget(self.playlist_btn)

        # ————— Search Card —————
        # ——— replace your old single‐input search bar with this ———
        search_box = BoxLayout(size_hint_y=None, height=50, spacing=10)

        # 1) Song title field
        self.title_input = TextInput(
            hint_text="Song title…",
            font_size=16,
            size_hint_x=0.4
        )
        search_box.add_widget(self.title_input)

        # 1) Artist name field
        self.artist_input = TextInput(
            hint_text="Artist name…",
            font_size=16,
            size_hint_x=0.4
        )
        search_box.add_widget(self.artist_input)

        # Search button stays the same, but will now read both inputs
        search_btn = Button(text="Search", font_size=16, size_hint_x=0.2)
        search_btn.bind(on_press=self.search_musicbrainz)
        search_box.add_widget(search_btn)

        # swap out the old search_box for this one
        root.add_widget(search_box)

        # ————— Results Section —————
        root.add_widget(Label(
            text="Results", font_size=20, color=(1,1,1,1),
            size_hint_y=None, height=30
        ))
        self.results_layout = GridLayout(
            cols=1, spacing=15, size_hint_y=None, padding=[0,5]
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.results_layout)
        root.add_widget(scroll)

        # ————— Back Button —————
        back_btn = Button(
            text="Back to Dashboard",
            size_hint_y=None, height=50,
            background_normal='', background_color=(0.13,0.13,0.2,1),
            color=(1,1,1,1), font_size=16
        )
        back_btn.bind(on_press=lambda _: setattr(self.screen_manager, 'current', 'dashboard'))
        root.add_widget(back_btn)

    def _update_bg(self, *args):
        self.bg_dark.pos = self.pos
        self.bg_dark.size = self.size
        self.bg_light.pos = (self.x, self.y + self.height * 0.6)
        self.bg_light.size = (self.width, self.height * 0.4)

    # … rest of your class unchanged …


    def open_playlist_popup(self, *_):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        for name in self.playlist_map:
            btn = Button(
                text=name,
                size_hint_y=None, height=40,
                background_normal='', background_color=(0.08,0.08,0.14,1),
                color=(1,1,1,1)
            )
            btn.bind(on_press=lambda inst, n=name: self.select_playlist(n))
            content.add_widget(btn)

        scroll = ScrollView(size_hint=(1,1))
        scroll.add_widget(content)
        popup = Popup(
            title="Choose Playlist",
            content=scroll,
            size_hint=(None,None), size=(320,450),
            background_color=(0.02,0.02,0.06,1),
            separator_color=(0.3,0.3,0.4,1)
        )
        self._popup = popup
        popup.open()

    def select_playlist(self, name):
        self.playlist_btn.text = name
        self._popup.dismiss()


    def search_musicbrainz(self, instance):
        # 2) read BOTH inputs
        title = self.title_input.text.strip()
        artist = self.artist_input.text.strip()

        # nothing to do if both empty
        if not (title or artist):
            return

        def fetch():
            try:
                # 3) build a URL with both params (backend will handle missing ones)
                parts = []
                if title:
                    parts.append(f"query={urllib.parse.quote(title)}")
                if artist:
                    parts.append(f"artist={urllib.parse.quote(artist)}")
                parts.append("limit=50")
                qs = "&".join(parts)

                url = f"http://127.0.0.1:8000/search/recording?{qs}"
                data = requests.get(url).json()
                Clock.schedule_once(lambda dt: self.display_results(data))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.display_results({"error": str(e)}))

        threading.Thread(target=fetch, daemon=True).start()



    def display_results(self, data):
        self.results_layout.clear_widgets()
        if "error" in data:
            self.results_layout.add_widget(Label(
                text=f"[color=ff3333]Error: {data['error']}[/color]",
                markup=True, font_size=16, size_hint_y=None, height=40
            ))
            return

        recs = data.get("recordings", [])
        if not recs:
            self.results_layout.add_widget(Label(
                text="No results found.",
                font_size=16, size_hint_y=None, height=40,
                color=(0.8,0.8,0.8,1)
            ))
            return

        for idx, item in enumerate(recs, 1):
            title = item.get("title", "Unknown")
            artist = item.get("artist-credit",[{}])[0].get("name","Unknown")
            card = BoxLayout(
                orientation='horizontal',
                size_hint_y=None, height=60,
                padding=[12,8], spacing=10
            )
            with card.canvas.before:
                Color(0.10,0.10,0.16,0.9)
                bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
            card.bind(pos=lambda w,p: setattr(bg,'pos',p),
                      size=lambda w,s: setattr(bg,'size',s))

            label = Label(
                text=f"[b]{idx}. {title}[/b]\n[i]{artist}[/i]",
                markup=True, font_size=16,
                color=(1,1,1,1),
                halign='left', valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            card.add_widget(label)

            add_btn = Button(
                text="Add",
                size_hint_x=None, width=80,
                background_normal='', background_color=(0.3,0.6,1,1),
                color=(1,1,1,1), font_size=16
            )
            add_btn.bind(on_press=lambda inst, t=title, a=artist: self.add_to_playlist(t,a))
            card.add_widget(add_btn)

            self.results_layout.add_widget(card)
    def update_playlist_map(self, new_map):
        # overwrite internal map
        self.playlist_map = new_map

        # reset the button text to the first playlist (or placeholder if empty)
        if new_map:
            first = next(iter(new_map.keys()))
            self.playlist_btn.text = first
        else:
            self.playlist_btn.text = "Select Playlist…"

    def add_to_playlist(self, title, artist):
        pid = self.playlist_map.get(self.playlist_btn.text)
        if not pid:
            self.results_layout.add_widget(Label(
                text="[color=ff4444]No playlist selected![/color]",
                markup=True, font_size=14, size_hint_y=None, height=30
            ))
            return

        def send():
            try:
                ea = urllib.parse.quote(artist)
                et = urllib.parse.quote(title)
                url = f"http://127.0.0.1:8000/add_song/{ea}/{et}/playlist/{pid}"
                res = requests.get(url).json()
                msg = res.get("message", "Added to playlist.")
                Clock.schedule_once(lambda dt: self._flash_message(msg))
            except Exception as e:
                Clock.schedule_once(lambda dt: self._flash_message(f"Error: {e}"))

        threading.Thread(target=send, daemon=True).start()

    def _flash_message(self, msg):
        lbl = Label(
            text=f"[color=88ff88]{msg}[/color]",
            markup=True, font_size=14,
            size_hint_y=None, height=30
        )
        self.results_layout.add_widget(lbl)
