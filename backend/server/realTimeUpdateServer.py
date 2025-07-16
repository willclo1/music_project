import asyncio
import websockets
import json
from sharedState import connected_clients

async def handler(websocket, path):
    email = await websocket.recv()
    connected_clients[email] = websocket
    print(f"{email} connected via WebSocket")

    try:
        async for message in websocket:
            data = json.loads(message)
            # Handle incoming messages if needed
    except websockets.ConnectionClosed:
        print(f"{email} disconnected")
        connected_clients.pop(email, None)

def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(handler, "localhost", 8765)
    loop.run_until_complete(server)
    loop.run_forever()