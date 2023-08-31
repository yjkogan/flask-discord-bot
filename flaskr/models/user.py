from flask import current_app

from flaskr.db import get_db
from .artist import Artist

class User:
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username
        self._artists = None

    @classmethod
    def create_from_db_row(cls, row):
        return cls(
            user_id=row["id"], username=row["username"]
        )

    @classmethod
    def get_or_create_for_discord_user(cls, discord_user):
        username = discord_user["username"]
        user = cls.get_by_username(username)
        if user is not None:
            return user
        
        return cls.create_user(username)

    @classmethod
    def get_by_id(cls, user_id):
        db = get_db()
        user = db.execute(
            "SELECT u.id, u.username FROM user u WHERE u.id = ?",
            (user_id,),
        ).fetchone()

        return cls.create_from_db_row(user)
    @classmethod
    def get_by_username(cls, username):
        db = get_db()
        user = db.execute(
            "SELECT u.id, u.username FROM user u WHERE u.username = ?",
            (username,),
        ).fetchone()
        if user is None:
            return None

        return cls.create_from_db_row(user)

    @classmethod
    def create_user(cls, username):
        db = get_db()
        current_app.logger.info(f"Creating user {username}")
        db.execute(
            "INSERT INTO user (username) VALUES (?)",
            (username,),
        )
        db.commit()
        return cls.get_by_username(username)

    def get_artists(self):
        return Artist.get_artists_for_user(self)
