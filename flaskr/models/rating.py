import sqlite3
from typing import Optional, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

from flaskr.db import get_db


class RatingExistsException(Exception):
    pass


class Rating:
    def __init__(self, id: int, type: str, name: str, value: float, user_id: int):
        self.id = id
        self.name = name
        self.type = type
        self.value = value
        self.user_id = user_id

    def __repr__(self):
        return f"Rating(id={self.id}, type={self.type}, name={self.name}, value={self.value}, user_id={self.user_id})"
    
    def __str__(self):
        return f'{self.name}:{self.type} ({self.value})'

    def update_value_property(self, new_value: float) -> Self:
        self.value = new_value
        return self

    @classmethod
    def create_from_db_row(cls, row: dict):
        return cls(id=row["id"], type=row["type"], name=row["name"], value=row["value"], user_id=row["user_id"])

    @classmethod
    def get_or_create_rating(cls, user: "User", rating_name: str, rating_type: str) -> Self:
        rating = cls.get_by_name_for_user(user=user, rating_name=rating_name, rating_type=rating_type)
        if rating is None:
            rating = cls.create_rating(user, rating_name, rating_type=rating_type)
        return rating

    @classmethod
    def get_ratings_for_user(cls, user: "User", rating_type: str):
        ratings = (
            get_db()
            .execute(
                "SELECT * FROM rating WHERE user_id = ? AND type = ? ORDER BY value ASC",
                (user.id, rating_type),
            )
            .fetchall()
        )
        return [cls.create_from_db_row(rating) for rating in ratings]

    @classmethod
    def create_rating(cls, user: "User", rating_name: str, rating_type: str, value: Optional[float] = None) -> Self:
        db = get_db()
        try:
            db.execute(
                "INSERT INTO rating (user_id, name, type, value) VALUES (?, ?, ?, ?)",
                (user.id, rating_name, rating_type, value),
            )
            db.commit()
            return cls.get_by_name_for_user(user, rating_name, rating_type)

        except sqlite3.IntegrityError as e:
            raise RatingExistsException(e)

    @classmethod
    def get_by_id_for_user(cls, user: "User", rating_id: int):
        rating = (
            get_db()
            .execute(
                "SELECT * FROM rating WHERE user_id = ? AND id = ?",
                (user.id, rating_id),
            )
            .fetchone()
        )
        if rating is None:
            return None
        return cls.create_from_db_row(rating)

    @classmethod
    def get_by_name_for_user(cls, user: "User", rating_name: str, rating_type: str):
        rating = (
            get_db()
            .execute(
                "SELECT * FROM rating WHERE user_id = ? AND name = ? AND type = ? COLLATE NOCASE",
                (user.id, rating_name, rating_type),
            )
            .fetchone()
        )
        if rating is None:
            return None
        return cls.create_from_db_row(rating)

    @classmethod
    def update_all_with_new_ratings(cls, user: "User", new_ratings: list[Self]):
        db = get_db()
        for rating in new_ratings:
            db.execute(
                'UPDATE rating'
                ' SET value = ?'
                ' WHERE name = ? AND user_id = ? AND type = ?',
                (rating.value, rating.name, user.id, rating.type)
            )
        db.commit()
