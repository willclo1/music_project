import socket

import json


class MySocket:

    def __init__(self,host="localhost",port=50000):

        self.sock = socket.socket()
        self.sock.connect((host, port))

    def request_action(self, username, playlist_id, action, target =None):
        data = {
            "action": action,
            "username": username,
            "playlist_id": playlist_id
        }
        if target:
            data["target"] = target
        json_data = json.dumps(data) + "\n"
        self.sock.send(json_data.encode('utf-8'))
    def request_users(self):
        data = {
            "request": "GET_USERS",
        }
        json_data = json.dumps(data) +"\n"
        self.sock.send(json_data.encode('utf-8'))

    def get_responses(self):
        buffer = ""
        responses = []

        # Set a short timeout to prevent hanging forever
        self.sock.settimeout(2.0)

        try:
            while True:
                chunk = self.sock.recv(1024).decode("utf-8")
                print(chunk)
                if not chunk:
                    break
                buffer += chunk

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    try:
                        parsed = json.loads(line.strip())
                        responses.append(parsed)
                    except json.JSONDecodeError as e:
                        print("JSON parsing error:", e)
        except socket.timeout:
            pass  # Graceful exit if server has finished sending

        print("Received responses:", responses)
        return responses

    def interpret_responses(self, responses):
        for resp in responses:
            if "status" in resp and "message" in resp:
                print(f"[{resp['status'].upper()}] {resp['message']}")
            elif "users" in resp:
                print("Connected Users:", resp["users"])
            elif "active_users" in resp or "waiting_users" in resp:
                print("Active:", resp.get("active_users", []))
                print("Waiting:", resp.get("waiting_users", []))
            else:
                print("Response:", resp)

    def listen_for_messages(self):
        while True:
            try:
                responses = self.get_responses()
                for resp in responses:
                    if "invite" in resp:
                        print("Received invite:", resp["invite"])
            except:
                break
