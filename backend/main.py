from fastapi import FastAPI, Query
import httpx
from backend import connect
import re

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
        data = response.json()

    if entity == "recording" and "recordings" in data:
        seen = set()
        deduped = []

        for rec in data["recordings"]:
            title = rec.get("title", "")
            artist = rec.get("artist-credit", [{}])[0].get("name", "")
            key = (title.lower(), artist.lower())

            if key not in seen and re.fullmatch(r"[A-Za-z0-9 ]+", title):
                seen.add(key)
                deduped.append(rec)

        data["recordings"] = deduped

    return data


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


    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    if result:
        return {"message": "User already exists", "user_id": result[0]}

    cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
    conn.commit()

    user_id = cursor.lastrowid
    return {"message": f"User '{username}' created", "user_id": user_id}


@app.get("/add_song/{artist}/{title}/playlist/{playlist_id}")
async def add_song(artist: str, title: str, playlist_id: int):
    cursor = conn.cursor()

    url = f"https://musicbrainz.org/ws/2/recording/?query=artist:{artist} AND recording:{title}&fmt=json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        answer = response.json()
    recordings = answer.get("recordings", [])

    if recordings:
        recordings = recordings[0]
        recording_title = recordings.get("title", "")
        recording_artist =artist
        duration = recordings.get("length")

        cursor.execute("insert into songs (title, artist, duration) VALUES (%s, %s, %s)", (recording_title, recording_artist, duration))

        cursor.execute(
            "SELECT song_id FROM songs WHERE title = %s AND artist = %s",
            (recording_title, recording_artist)
        )
        song_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT MAX(position) FROM playlist_songs WHERE playlist_id = %s",
            (playlist_id,)
        )
        current_max = cursor.fetchone()[0] or 0
        new_position = current_max + 1


        cursor.execute(
            "INSERT INTO playlist_songs (playlist_id, song_id, position) VALUES (%s, %s, %s)",
            (playlist_id, song_id, new_position)
        )
        conn.commit()


        return {
            "status": "success",
            "message": f"'{recording_title}' added to playlist #{playlist_id}",
            "song_id": song_id,
            "position": new_position,
        }

    else:
        return {"status": "failure", "message": "Song not found on MusicBrainz"}


@app.get("/get_playlists/{user_id}")
async def get_playlists(user_id: int):
    cursor = conn.cursor()
    cursor.execute("SELECT name, playlist_id FROM playlists WHERE user_id = %s", (user_id,))
    results = cursor.fetchall()

    playlists = [{"name": name, "id": pid} for name, pid in results]

    return {"playlists": playlists}
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.get("/get_user_id/{email}")
async def get_user_id(email: str):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    uid = cursor.fetchone()
    return {"user_id": uid[0] if uid else None}