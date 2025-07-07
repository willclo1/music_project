from fastapi import FastAPI, Query
import httpx
import connect
app = FastAPI()

conn = connect.connect()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/search/{entity}")
async def search_entity(
    entity: str,
    query: str = Query(...),
    limit: int = Query(25),
    offset: int = Query(0)
):
    url = f"https://musicbrainz.org/ws/2/{entity}?query={query}&limit={limit}&offset={offset}&fmt=json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


@app.post("/create_playlist/{name}/{email}")
def create_playlist(name: str, email: str):
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()

    if not result:
        return {"error": f"No user found with email '{email}'"}

    user_id = result[0]

    # Insert the playlist for the user
    cursor.execute("INSERT INTO playlists (name, user_id) VALUES (%s, %s)", (name, user_id))
    conn.commit()

    playlist_id = cursor.lastrowid
    return {
        "message": f"Playlist '{name}' created for user '{email}'",
        "playlist_id": playlist_id,
        "user_id": user_id
    }


@app.post("/create_user/{username}/{email}")
def create_user(username: str, email: str):
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    if result:
        return {"message": "User already exists", "user_id": result[0]}

    # Insert new user
    cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
    conn.commit()

    user_id = cursor.lastrowid
    return {"message": f"User '{username}' created", "user_id": user_id}








@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
