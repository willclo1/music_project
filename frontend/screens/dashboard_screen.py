from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
import threading
import requests

class DashboardScreen(BoxLayout):
    def __init__(self, user_email, **kwargs):
        super().__init__(orientation='vertical', spacing=20, padding=40, **kwargs)
        self.user_email = user_email
        self.playlist_map = {}

        # Background styling
        with self.canvas.before:
            Color(0.07, 0.07, 0.12, 1)
            self.bg = RoundedRectangle(radius=[0], pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        self.add_widget(Label(text="Playlist Creator", font_size=32, bold=True,
                              size_hint_y=None, height=60, color=(0.9, 0.9, 1, 1)))

        # Section: Playlist Creation
        self.add_widget(Label(text="Create New Playlist", font_size=18, size_hint_y=None, height=30))

        playlist_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        self.playlist_input = TextInput(hint_text="Playlist name", font_size=16)
        create_btn = Button(text="Create", font_size=16, size_hint_x=None, width=120,
                            background_color=[0.6, 0.4, 1, 1])
        create_btn.bind(on_press=self.create_playlist)
        playlist_box.add_widget(self.playlist_input)
        playlist_box.add_widget(create_btn)
        self.add_widget(playlist_box)

        # Section: Playlist Selector
        self.add_widget(Label(text="Your Playlists", font_size=18, size_hint_y=None, height=30))
        self.playlist_spinner = Spinner(text="Choose playlist", values=[], font_size=16,
                                        size_hint_y=None, height=50,
                                        background_color=[0.2, 0.2, 0.3, 1], color=[1, 1, 1, 1])
        self.add_widget(self.playlist_spinner)
        self.populate_playlists()

        # Section: Search Music
        self.add_widget(Label(text="Search for Songs", font_size=18, size_hint_y=None, height=30))
        search_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        self.query_input = TextInput(hint_text="Search MusicBrainz", font_size=16)
        search_btn = Button(text="Search", size_hint_x=None, width=120, font_size=16,
                            background_color=[0.2, 0.6, 1, 1])
        search_btn.bind(on_press=self.search_musicbrainz)
        search_box.add_widget(self.query_input)
        search_box.add_widget(search_btn)
        self.add_widget(search_box)

        # Section: Results
        self.add_widget(Label(text="Search Results", font_size=18, size_hint_y=None, height=30))
        self.results_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.results_layout)
        self.add_widget(scroll)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


    def populate_playlists(self):
        def fetch():
            try:
                email = self.user_email
                url = f"http://127.0.0.1:8000/get_user_id/{email}"  # Optional: if you need to resolve user_id from email
                res = requests.get(url)
                user_id = res.json().get("user_id")

                playlist_url = f"http://127.0.0.1:8000/get_playlists/{user_id}"
                playlist_res = requests.get(playlist_url)
                data = playlist_res.json().get("playlists", [])

                def update_ui(dt):
                    self.playlist_map = {item["name"]: item["id"] for item in data}
                    self.playlist_spinner.values = list(self.playlist_map.keys())

                Clock.schedule_once(update_ui)

            except Exception as e:
                error_msg = str(e)
                Clock.schedule_once(lambda dt: self.results_layout.add_widget(
                    Label(text=f"⚠️ Error loading playlists: {error_msg}", font_size=14)
                ))

        threading.Thread(target=fetch, daemon=True).start()
    def search_musicbrainz(self, instance):
        query = self.query_input.text.strip()
        if not query:
            return

        def fetch():
            try:
                url = f"http://127.0.0.1:8000/search/recording?query={query}&limit=50"
                res = requests.get(url)
                data = res.json()
                Clock.schedule_once(lambda dt: self.display_results(data))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.display_results({"error": str(e)}))

        threading.Thread(target=fetch, daemon=True).start()

    def create_playlist(self, instance):
        name = self.playlist_input.text.strip()
        if not name:
            return

        def send():
            try:
                email = self.user_email
                url = f"http://127.0.0.1:8000/create_playlist/{name}/{email}"
                response = requests.post(url)
                result = response.json()
                playlist_id = result.get("playlist_id")

                self.playlist_map[name] = playlist_id

                def update_ui(dt):
                    self.playlist_spinner.values = list(self.playlist_map.keys())
                    self.results_layout.add_widget(Label(text=f"{result.get('message', '')}", font_size=14))

                Clock.schedule_once(update_ui)

            except Exception as e:
                error_message = str(e)

                def show_error(dt):
                    self.results_layout.add_widget(Label(text=f"⚠Error: {error_message}", font_size=14))

                Clock.schedule_once(show_error)

        threading.Thread(target=send, daemon=True).start()

    def display_results(self, data):
        self.results_layout.clear_widgets()

        if "error" in data:
            self.results_layout.add_widget(Label(text=f"Error: {data['error']}", font_size=16))
            return

        results = data.get("recordings", [])
        if not results:
            self.results_layout.add_widget(Label(text="No results found.", font_size=16))
            return

        for item in results:
            title = item.get("title", "Unknown Title")
            artist = item.get("artist-credit", [{}])[0].get("name", "Unknown Artist")

            song_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
            label = Label(text=f"{title} by {artist}", font_size=16)
            add_btn = Button(text="Add", size_hint_x=None, width=80)


            add_btn.bind(on_press=lambda inst, t=title, a=artist: self.add_to_playlist(t, a))

            song_box.add_widget(label)
            song_box.add_widget(add_btn)
            self.results_layout.add_widget(song_box)

    def add_to_playlist(self, t, a):
        def send():
            try:
                selected_name = self.playlist_spinner.text
                playlist_id = self.playlist_map.get(selected_name)

                if not playlist_id:
                    Clock.schedule_once(lambda dt: self.results_layout.add_widget(
                        Label(text="Please select a playlist first!", font_size=14)
                    ))
                    return

                url = f"http://127.0.0.1:8000/add_song/{a}/{t}/playlist/{playlist_id}"
                response = requests.get(url)
                result = response.json()

                Clock.schedule_once(lambda dt: self.results_layout.add_widget(
                    Label(text=f"{result.get('message', '')}", font_size=14)
                ))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.results_layout.add_widget(
                    Label(text=f"Error: {str(e)}", font_size=14)
                ))

        threading.Thread(target=send, daemon=True).start()