from kivy.clock import Clock
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineAvatarListItem, IconLeftWidget
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.snackbar import MDSnackbar
from kivy.metrics import dp
import threading
from functools import partial
import requests

class FriendsCenter(MDScreen):
    def __init__(self, user_email, friend_list, socket,**kwargs):
        super().__init__(**kwargs)
        self.user_email = user_email
        self.friend_list = friend_list
        self.socket = socket
        self.selected_playlist_id = None
        self.playlist_map = {}

        layout = MDBoxLayout(orientation='vertical')

        layout.add_widget(MDTopAppBar(title="Friends Center 🎶", elevation=4))

        self.playlist_button = MDRaisedButton(
            text="Choose a playlist",
            size_hint_y=None,
            height=dp(48),
            pos_hint={"center_x": 0.5}
        )
        layout.add_widget(self.playlist_button)

        scroll = MDScrollView()
        self.list_widget = MDList()


        scroll.add_widget(self.list_widget)
        layout.add_widget(scroll)

        invite_label = MDLabel(
            text="Received Invites",
            halign="center",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(32),
            padding=(dp(10), dp(10))
        )
        layout.add_widget(invite_label)

        # Invite display scroll list
        self.invite_scroll = MDScrollView()
        self.invite_list_widget = MDList()
        self.invite_scroll.add_widget(self.invite_list_widget)
        layout.add_widget(self.invite_scroll)

        self.add_widget(layout)

        self.dropdown_menu = MDDropdownMenu(
            caller=self.playlist_button,
            items=[],
            width_mult=4
        )
        self.playlist_button.bind(on_release=lambda *args: self.dropdown_menu.open())

        self.build_friend_list()
        self.populate_playlists()
        self.fetch_invites()

    def select_playlist(self, name):
        self.playlist_button.text = name
        self.selected_playlist_id = self.playlist_map.get(name)
        self.dropdown_menu.dismiss()

    def handle_received_invites(self, invite_list):
        self.invite_list_widget.clear_widgets()

        if not invite_list:
            self.invite_list_widget.add_widget(
                OneLineAvatarListItem(text="No invites received 🎁")
            )
            return

        for invite in invite_list:
            from_user = invite.get("from", "Unknown Sender")
            playlist_name = invite.get("playlist_name", "Unnamed Playlist")

            item = OneLineAvatarListItem(
                text=f"{from_user} invited you to '{playlist_name}'"
            )
            item.add_widget(IconLeftWidget(icon="account"))
            self.invite_list_widget.add_widget(item)

    def build_friend_list(self):
        self.list_widget.clear_widgets()
        added = False

        for friend in sorted(self.friend_list):
            if friend != self.user_email:
                item = OneLineAvatarListItem(
                    text=friend,
                    on_release=partial(self.invite_friend, friend)
                )
                item.add_widget(IconLeftWidget(icon="account"))
                self.list_widget.add_widget(item)
                added = True

        if not added:
            self.list_widget.add_widget(
                OneLineAvatarListItem(text="No collaborators available.")
            )

    def invite_friend(self, friend, *args):
        if not self.selected_playlist_id:
            MDSnackbar("Please select a playlist before inviting").open()
            return

        try:
            self.start_collab_with_friend(friend)
            MDSnackbar("Invite sent to {friend}").open()
        except Exception as e:
            print("Invite error:", e)
            MDSnackbar("Invite failed").open()

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

    def _build_dropdown_menu(self):
        def create_menu_callback(name):
            return lambda: self.select_playlist(name)

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": name,
                "on_release": create_menu_callback(name)
            }
            for name in self.playlist_map.keys()
        ]

        self.dropdown_menu.items = menu_items

    def start_collab_with_friend(self, friend):
        selected_name = self.playlist_button.text
        playlist_id = self.playlist_map.get(selected_name)

        if not playlist_id:
            MDSnackbar(text="Oops! No playlist selected").open()
            return

        try:
            self.socket.request_action(
                username=self.user_email,
                playlist_id=playlist_id,
                action="INVITE",
                target=friend
            )
            print(f"Invite sent to {friend} on playlist ID {playlist_id}")
            MDSnackbar("Collab invite sent to {friend}").open()
        except Exception as e:
            print("Collab start error:", e)
            MDSnackbar("Failed to send invite").open()

    def close_socket(self):
        if hasattr(self, "socket") and self.socket:
            try:
                self.socket.sock.close()
                self.socket = None
                print("Socket connection closed.")
            except Exception as e:
                print("Socket close error:", e)

    def fetch_invites(self):
        def _fetch_invites():
            try:

                self.socket.request_invites(self.user_email, self.selected_playlist_id)
                responses = self.socket.get_responses()

                invite_list = []
                for resp in responses:
                    invite_list.extend(resp.get("invites", []))

                Clock.schedule_once(lambda dt: self.handle_received_invites(invite_list))
            except Exception as e:
                print("Invite fetch error:", e)

        threading.Thread(target=_fetch_invites, daemon=True).start()