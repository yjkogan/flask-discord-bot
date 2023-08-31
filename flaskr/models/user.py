from flaskr.db import get_db
from .artist import Artist

class User:
    def __init__(self, user_id, username, discord_id):
        self.id = user_id
        self.username = username
        self.discord_id = discord_id
        self._artists = None

    @classmethod
    def get_or_create_for_discord_user(cls, discord_user):
        username = discord_user["username"]
        user = cls.get_by_username(username)

        if user is None:
            db = get_db()
            db.execute(
                "INSERT INTO user (username, discord_id)" " VALUES (?, ?)",
                (username, discord_user["id"]),
            )
            db.commit()

        return cls.get_by_username(username)

    @classmethod
    def get_by_id(cls, user_id):
        db = get_db()
        user = db.execute(
            "SELECT u.id, u.username, u.discord_id FROM user u WHERE u.id = ?",
            (user_id,),
        ).fetchone()

        return cls(
            user_id=user["id"], username=user["username"], discord_id=user["discord_id"]
        )
    @classmethod
    def get_by_username(cls, username):
        db = get_db()
        user = db.execute(
            "SELECT u.id, u.username, u.discord_id FROM user u WHERE u.username = ?",
            (username,),
        ).fetchone()
        if user is None:
            return None

        return cls(
            user_id=user["id"], username=user["username"], discord_id=user["discord_id"]
        )

    def get_artists(self):
        if self._artists is not None:
            return self._artists
        self._artists = Artist.get_artists_for_user(self)
        return self._artists
