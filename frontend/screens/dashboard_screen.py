from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDFloatingActionButton, MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
import threading
import requests
import json

from frontend.client import MySocket


class DashboardScreen(MDScreen):
    def __init__(self, user_email, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.user_email = user_email
        self.screen_manager = screen_manager
        self.playlist_map = {}

        self.md_bg_color = get_color_from_hex("#101320")

        # Main layout
        root = MDBoxLayout(orientation="vertical", spacing=24, padding=[32, 32, 32, 32])
        self.add_widget(root)

        # Header
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=64)
        header.add_widget(MDLabel(
            text="Playlist Studio",
            font_style="H4",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        ))
        header.add_widget(MDLabel(
            text=self.user_email,
            font_style="Subtitle1",
            halign="right",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        ))
        root.add_widget(header)

        # Collaborator Display Section
        self.collab_label = MDLabel(
            text="Available Collaborators:",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=32
        )

        self.collab_list = MDBoxLayout(
            orientation="vertical",
            spacing=8,
            size_hint_y=None,
            height=120
        )

        root.add_widget(self.collab_label)
        root.add_widget(self.collab_list)

        # Cards container (vertically centered)
        cards_row = MDBoxLayout(
            spacing=24,
            size_hint=(1, None),
            height=340,
            pos_hint={"center_y": 0.7}
        )

        # Create Playlist Card
        create_card = MDCard(
            orientation="vertical",
            padding=24,
            spacing=16,
            size_hint=(0.5, None),
            height=320,
            md_bg_color=get_color_from_hex("#1E202A"),
            radius=[16],
            elevation=12
        )
        create_card.add_widget(MDLabel(
            text="Create Playlist",
            font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        ))
        self.playlist_input = MDTextField(
            hint_text="Playlist name",
            mode="rectangle",
            size_hint_y=None,
            height=50
        )
        btn_collaborate = MDRaisedButton(
            text="Collaborate",
            size_hint=(None, None),
            size=(160, 48),
            md_bg_color=get_color_from_hex("#00BCD4"),  # Optional: distinct color
            pos_hint={"center_x": 0.5}
        )
        btn_collaborate.bind(on_release=lambda *args: self.collaborate())
        create_card.add_widget(btn_collaborate)
        create_card.add_widget(self.playlist_input)
        btn_create = MDRaisedButton(
            text="Create",
            size_hint=(None, None),
            size=(160, 48),
            md_bg_color=get_color_from_hex("#4D88FF"),
            pos_hint={"center_x": 0.5}
        )
        btn_create.bind(on_release=self.create_playlist)
        create_card.add_widget(btn_create)
        cards_row.add_widget(create_card)

        # Select Playlist Card
        select_card = MDCard(
            orientation="vertical",
            padding=24,
            spacing=16,
            size_hint=(0.5, None),
            height=320,
            md_bg_color=get_color_from_hex("#1E202A"),
            radius=[16],
            elevation=12
        )
        select_card.add_widget(MDLabel(
            text="Select Playlist",
            font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        ))
        self.playlist_button = MDFlatButton(
            text="Choose...",
            size_hint=(None, None),
            size=(240, 48),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            md_bg_color=get_color_from_hex("#2C2E3A"),
            pos_hint={"center_x": 0.5}
        )
        select_card.add_widget(self.playlist_button)
        btn_open = MDRaisedButton(
            text="Open",
            size_hint=(None, None),
            size=(160, 48),
            md_bg_color=get_color_from_hex("#3C70D6"),
            pos_hint={"center_x": 0.5}
        )
        btn_open.bind(on_release=self.open_playlist_detail)
        select_card.add_widget(btn_open)
        cards_row.add_widget(select_card)

        center_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            padding=[0, 60, 0, 0]  # add space above
        )

        center_box.add_widget(Widget())  # pushes content down
        center_box.add_widget(cards_row)
        center_box.add_widget(Widget())  # pushes content up

        root.add_widget(center_box)

        # Floating Song Search Button
        self.fab = MDFloatingActionButton(
            icon="magnify",
            md_bg_color=get_color_from_hex("#26C6DA"),
            pos_hint={"center_x": 0.5, "center_y": 0.05}
        )
        self.fab.bind(on_release=self.go_to_search)
        self.add_widget(self.fab)

        # Fetch playlists
        self.populate_playlists()

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
                    self._build_dropdown_menu()

                Clock.schedule_once(ui)
            except Exception as e:
                print("Playlist load error:", e)
        threading.Thread(target=_fetch, daemon=True).start()

    def create_playlist(self, *args):
        name = self.playlist_input.text.strip()
        if not name:
            return

        def _send():
            try:
                res = requests.post(
                    f"http://127.0.0.1:8000/create_playlist/{name}/{self.user_email}"
                ).json()
                pid = res.get("playlist_id")
                self.playlist_map[name] = pid

                def ui(dt):
                    self._build_dropdown_menu()

                Clock.schedule_once(ui)
            except Exception as e:
                print("Create error:", e)
        threading.Thread(target=_send, daemon=True).start()

    def _build_dropdown_menu(self):
        def create_menu_callback(name):
            return lambda: self.select_playlist(name)

        menu_items = [
            {"viewclass": "OneLineListItem", "text": name,
             "on_release": create_menu_callback(name)}
            for name in self.playlist_map.keys()
        ]

        if hasattr(self, 'dropdown_menu'):
            self.dropdown_menu.items = menu_items
        else:
            self.dropdown_menu = MDDropdownMenu(
                caller=self.playlist_button,
                items=menu_items,
                width_mult=4
            )
            self.playlist_button.bind(on_release=lambda *args: self.dropdown_menu.open())

    def select_playlist(self, name):
        self.playlist_button.text = name
        self.dropdown_menu.dismiss()

    def open_playlist_detail(self, *args):
        sel = self.playlist_button.text
        pid = self.playlist_map.get(sel)
        if not pid:
            return

        from frontend.screens.playlist_details_screen import PlaylistDetailScreen
        if not self.screen_manager.has_screen("playlist_detail"):
            self.screen_manager.add_widget(PlaylistDetailScreen(name="playlist_detail"))

        screen = self.screen_manager.get_screen("playlist_detail")
        screen.load_playlist(self.user_email, pid)
        self.screen_manager.current = "playlist_detail"



    def go_to_search(self, *args):
        from frontend.screens.search_screen import SearchScreen
        if not self.screen_manager.has_screen("search"):
            self.screen_manager.add_widget(SearchScreen(
                playlist_map=self.playlist_map,
                screen_manager=self.screen_manager,
                name="search"
            ))
        else:
            self.screen_manager.get_screen("search").update_playlist_map(self.playlist_map)

        self.screen_manager.current = "search"

    def collaborate(self):
        def _fetch_friends():
            try:
                # Step 1: Tell the server you're looking to collaborate (WAITING)
                if not hasattr(self, 'socket') or self.socket is None:
                    self.socket = MySocket(host="localhost", port=50000)
                    self.socket.request_action(username=self.user_email, playlist_id=None, action="WAITING")

                # Step 2: Now fetch list of others who are also WAITING
                self.socket.request_users()

                responses = self.socket.get_responses()
                print(responses)
                friends = set()

                for resp in responses:
                    friends.update(resp.get("waiting_users", []))
                    friends.update(resp.get("active_users", []))

                print(friends)
                # Optionally convert back to list if needed
                friends = list(friends)

                def ui(dt):
                    self._render_user_list(friends)

                Clock.schedule_once(ui)
            except Exception as e:
                print("Friend fetch error:", e)

        threading.Thread(target=_fetch_friends, daemon=True).start()


    def start_collab_with_friend(self, friend):

        sel = self.playlist_button.text
        playlist_id = self.playlist_map.get(sel)
        if not playlist_id:
            print("No playlist selected")
            return

        # Send JOIN action to collab server for both users
        try:
            self.socket.request_action(username=self.user_email, playlist_id=playlist_id, action="INVITE", target=friend)

            print(f"Invite sent to {friend} on playlist ID {playlist_id}")
        except Exception as e:
            print("Collab start error:", e)

    def _render_user_list(self, friend_list):
        self.collab_list.clear_widgets()

        for friend in sorted(friend_list):
            if friend != self.user_email:
                friend_card = MDCard(
                    size_hint_y=None,
                    height=64,
                    md_bg_color=get_color_from_hex("#2C2E3A"),
                    radius=[12],
                    elevation=6,
                    padding=[8, 8, 8, 8],
                )

                inner_box = MDBoxLayout(
                    orientation="horizontal",
                    spacing=12,
                    size_hint=(1, None),
                    height=48,
                    pos_hint={"center_y": 0.5}
                )

                avatar = MDIconButton(
                    icon="account",
                    theme_text_color="Custom",
                    text_color=(0.7, 0.9, 1, 1),
                    size_hint=(None, None),
                    size=(32, 32),
                    pos_hint={"center_y": 0.5}
                )

                name_label = MDLabel(
                    text=friend,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    font_style="Subtitle1",
                    halign="left",
                    valign="middle"
                )

                collab_button = MDRaisedButton(
                    text="Invite",
                    md_bg_color=get_color_from_hex("#00BCD4"),
                    size_hint=(None, None),
                    size=(100, 36),
                    pos_hint={"center_y": 0.5},
                    on_release=lambda x, f=friend: self.start_collab_with_friend(f)
                )

                inner_box.add_widget(avatar)
                inner_box.add_widget(name_label)
                inner_box.add_widget(collab_button)
                friend_card.add_widget(inner_box)
                self.collab_list.add_widget(friend_card)

    def close_socket(self):
        if hasattr(self, 'socket') and self.socket:
            self.socket.sock.close()
            self.socket = None