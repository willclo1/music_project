import socket
import threading

from enum import Enum

import json

class CollaborationServer:
    def __init__(self, host='localhost', port=50000):
        self.host = host
        self.port = port
        self.serversocket = socket.socket()
        self.active_users = {}
        self.actions = []
        self.waiting_users = set()
        self.user_lock = threading.Lock()



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

    def handle_join(self, username, playlist_id, clientsocket):
        with self.user_lock:
            self.active_users[username] = playlist_id
        print(f"Joining {username} to playlist {playlist_id}")
        response = {"status": "ok", "message": f"{username} joined"}
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

        response = {"status": "ok", "message": f"{target_username} invite sent"}
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

                    if request == 'GET_USERS':
                        self.handle_get_users(clientsocket)
                    elif action == 'WAITING':
                        self.handle_waiting(username, clientsocket)
                    elif action == "JOIN":
                        self.handle_join(username, playlist_id, clientsocket)
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