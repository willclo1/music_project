import socket
import threading
from sharedState import active_users, user_invites, user_lock

from enum import Enum

import json

import requests


class CollaborationServer:
    def __init__(self, host='localhost', port=50000):
        self.host = host
        self.port = port
        self.serversocket = socket.socket()
        self.active_users = active_users
        self.actions = []
        self.user_invites = user_invites

        self.waiting_users = set()
        self.user_lock = user_lock



    def handle_client(self, clientsocket, addr):
        print(f"Handling {addr}")
        try:
            self.receive_data(clientsocket, addr)
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            clientsocket.close()

    def handle_waiting(self, username, clientsocket):
        with self.user_lock:
            self.waiting_users.add(username)
        print(f"{username} is waiting")
        response = {"status": "ok", "message": f"{username} registered as waiting"}
        clientsocket.send((json.dumps(response) + "\n").encode('utf-8'))


    def handle_sync(self, username, playlist_id, clientsocket):
        print(f"Syncing data for {username} in playlist {playlist_id}")
        response = {"status": "ok", "message": f"{username}'s playlist synced"}
        clientsocket.send((json.dumps(response) + "\n").encode('utf-8'))

    def handle_leave(self, username, playlist_id, clientsocket):
        print(f"Leaving: {username}")
        with self.user_lock:
            if username not in self.users:
                self.users.remove(username)
        response = {"status": "ok", "message": f"{username} left"}
        clientsocket.send((json.dumps(response) + "\n").encode('utf-8'))

    def handle_get_users(self, clientsocket):
        with self.user_lock:
            active = list(self.active_users.keys())
            waiting = list(self.waiting_users)
        response = {
            "active_users": active,
            "waiting_users": waiting
        }
        print(response)
        clientsocket.send((json.dumps(response) + "\n").encode('utf-8'))
    def handle_invite(self, username,target_username,playlist_id, clientsocket):
        print(f"{username }Inviting {target_username} to join playlist {playlist_id}")
        invite = {
            "from" : username,
            "playlist_id" : playlist_id,
        }
        self.user_invites.setdefault(target_username, []).append(invite)
        response = {"status": "ok", "message": f"{target_username} invite sent"}
        clientsocket.send((json.dumps(response) + "\n").encode('utf-8'))


    def handle_get_invite(self, clientsocket, username):
        invites = self.user_invites.get(username, [])
        print("Raw invites:", invites)

        enriched_invites = []

        for invite in invites:
            if not isinstance(invite, dict):
                continue

            sender_email = invite.get("from")
            pid = invite.get("playlist_id")

            # Step 1: Get sender's user_id
            try:
                user_id_resp = requests.get(f"http://127.0.0.1:8000/get_user_id/{sender_email}")
                sender_id = user_id_resp.json().get("user_id")
            except Exception as e:
                print(f"Error fetching user ID for {sender_email}:", e)
                sender_id = None

            # Step 2: Get sender's playlists
            playlist_name = "Unnamed Playlist"
            if sender_id:
                try:
                    playlists_resp = requests.get(f"http://127.0.0.1:8000/get_playlists/{sender_id}")
                    playlists = playlists_resp.json().get("playlists", [])
                    playlist_map = {p["id"]: p["name"] for p in playlists}
                    playlist_name = playlist_map.get(pid, playlist_name)
                except Exception as e:
                    print(f"Error fetching playlists for {sender_email}:", e)

            # Step 3: Enrich invite
            enriched_invite = {
                "from": sender_email,
                "playlist_id": pid,
                "playlist_name": playlist_name
            }

            enriched_invites.append(enriched_invite)

        print("Enriched invites:", enriched_invites)
        clientsocket.send((json.dumps(enriched_invites) + "\n").encode('utf-8'))

    def handle_accept_invite(self, username, playlist_id, clientsocket, target):
        invites = self.user_invites.get(username, [])
        self.user_invites[username] = [
            i for i in invites if not (
                    i.get("from") == target and i.get("playlist_id") == playlist_id
            )
        ]
        with self.user_lock:
            self.active_users.setdefault(playlist_id, set()).add(username)
            self.active_users[playlist_id].add(target)

        response = {"status": "ok", "message": f"{username} joined collab on playlist {playlist_id}"}

        clientsocket.send((json.dumps(response) + "\n").encode('utf-8'))


    def start(self):
        self.serversocket.bind((self.host, self.port))
        self.serversocket.listen(1)

        print(f"Collaboration Server running on {self.host}:{self.port}")
        while True:
            clientsocket, addr = self.serversocket.accept()
            threading.Thread(target=self.handle_client, args=(clientsocket, addr), daemon=True).start()

    def receive_data(self, clientsocket, addr):
        buffer = ""

        while True:
            try:
                chunk = clientsocket.recv(1024).decode('utf-8')
                if not chunk:
                    break
                buffer += chunk

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    parsed = json.loads(line.strip())
                    print("Received:", parsed)

                    action = parsed.get('action')
                    request = parsed.get('request')
                    username = parsed.get('username')
                    playlist_id = parsed.get('playlist_id')
                    target = parsed.get('target')
                    if request == 'GET_USERS':
                        self.handle_get_users(clientsocket)
                    elif request == 'GET_INVITES':
                        self.handle_get_invite(clientsocket, username)
                    elif action == 'ACCEPT':
                        self.handle_accept_invite(username, playlist_id, clientsocket, target)
                    elif action == 'WAITING':
                        self.handle_waiting(username, clientsocket)
                    elif action == "SYNC":
                        self.handle_sync(username, playlist_id, clientsocket)
                    elif action == "LEAVE":
                        self.handle_leave(username, playlist_id, clientsocket)
                    elif action == "INVITE":
                        self.handle_invite(username, parsed.get("target"), playlist_id, clientsocket)
                    else:
                        error = {"status": "error", "message": "Unknown action"}
                        clientsocket.send((json.dumps(error) + "\n").encode('utf-8'))

            except Exception as e:
                print(f"Connection error with {addr}: {e}")
                break

        clientsocket.close()




if __name__ == '__main__':
    server = CollaborationServer()
    server.start()