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

    url = f"https://musicbrainz.org/ws/2/recording/?query=artist:{artist}%20AND%20recording{title}&fmt=json"
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





@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
