import mariadb
import sys
def connect():
    try:
        conn = mariadb.connect(
            user="root",
            password="root",
            host="localhost",
            port=3306,
            database="music"
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)