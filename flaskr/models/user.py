from typing import Optional
from flask import current_app

from flaskr.db import get_db
from .rating import Rating

class User:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username

    @classmethod
    def create_from_db_row(cls, row: dict):
        return cls(
            user_id=row["id"], username=row["username"]
        )

    @classmethod
    def get_or_create_for_discord_user(cls, discord_user: dict):
        username: str = discord_user["username"]
        user = cls.get_by_username(username)
        if user is not None:
            return user
        
        return cls.create_user(username)

    @classmethod
    def get_by_id(cls, user_id: int):
        db = get_db()
        user: dict = db.execute(
            "SELECT u.id, u.username FROM user u WHERE u.id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            return None

        return cls.create_from_db_row(user)

    @classmethod
    def get_by_username(cls, username: str):
        db = get_db()
        user = db.execute(
            "SELECT u.id, u.username FROM user u WHERE u.username = ?",
            (username,),
        ).fetchone()
        if user is None:
            return None

        return cls.create_from_db_row(user)

    @classmethod
    def create_user(cls, username: str):
        db = get_db()
        current_app.logger.info(f"Creating user {username}")
        db.execute(
            "INSERT INTO user (username) VALUES (?)",
            (username,),
        )
        db.commit()
        return cls.get_by_username(username)

    def get_ratings(self, rating_type: str) -> list[Rating]:
        return Rating.get_ratings_for_user(self, rating_type)
