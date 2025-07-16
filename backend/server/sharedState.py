# shared_state.py
from threading import Lock

active_users = {}         # playlist_id → set of usernames
user_invites = {}         # username → list of invites
connected_clients = {}    # username → websocket
user_lock = Lock()