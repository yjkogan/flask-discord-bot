import sqlite3
from typing import Optional, TYPE_CHECKING
from typing_extensions import Self

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
        return f"{self.name}:{self.type} ({self.value})"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Rating):
            return NotImplemented
        return self.id == __value.id

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "user_id": self.user_id,
        }

    def update_value_property(self, new_value: float) -> Self:
        self.value = new_value
        return self

    @classmethod
    def create_from_db_row(cls, row: dict):
        return cls(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            value=row["value"],
            user_id=row["user_id"],
        )

    @classmethod
    def get_or_create_rating(
        cls, user: "User", rating_name: str, rating_type: str
    ) -> Self:
        rating = cls.get_by_name_for_user(
            user=user, rating_name=rating_name, rating_type=rating_type
        )
        if rating is None:
            rating = cls.create_rating(user, rating_name, rating_type=rating_type)
        return rating

    @classmethod
    def get_ratings_for_user(cls, user: "User"):
        ratings = []
        with get_db().cursor() as cursor:
            cursor.execute(
                "SELECT * FROM rating WHERE user_id = %s ORDER BY value ASC",
                (user.id,),
            )
            ratings = cursor.fetchall()
        return [cls.create_from_db_row(rating) for rating in ratings]

    @classmethod
    def get_ratings_types_for_user(cls, user: "User") -> list[str]:
        ratings = []
        with get_db().cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT type FROM rating WHERE user_id = %s ORDER BY type ASC",
                (user.id,),
            )
            ratings = cursor.fetchall()
        return [rating["type"] for rating in ratings]

    @classmethod
    def create_rating(
        cls,
        user: "User",
        rating_name: str,
        rating_type: str,
        value: Optional[float] = None,
    ) -> Self:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO rating (user_id, name, type, value) VALUES (%s, %s, %s, %s)",
                (user.id, rating_name, rating_type, value),
            )
        db.commit()
        return cls.get_by_name_for_user(user, rating_name, rating_type)

    @classmethod
    def get_by_id_for_user(cls, user: "User", rating_id: int):
        rating = None
        with get_db().cursor() as cursor:
            cursor.execute(
                "SELECT * FROM rating WHERE user_id = %s AND id = %s",
                (user.id, rating_id),
            )
            rating = cursor.fetchone()
        if rating is None:
            return None
        return cls.create_from_db_row(rating)

    @classmethod
    def get_by_name_for_user(cls, user: "User", rating_name: str, rating_type: str):
        rating = None
        with get_db().cursor() as cursor:
            cursor.execute(
                "SELECT * FROM rating WHERE user_id = %s AND LOWER(name) = LOWER(%s) AND LOWER(type) = LOWER(%s)",
                (user.id, rating_name, rating_type),
            )
            rating = cursor.fetchone()

        if rating is None:
            return None
        return cls.create_from_db_row(rating)

    @classmethod
    def update_all_with_new_ratings(cls, user: "User", new_ratings: list[Self]):
        db = get_db()
        with db.cursor() as cursor:
            for rating in new_ratings:
                cursor.execute(
                    "UPDATE rating"
                    " SET value = %s"
                    " WHERE name = %s AND user_id = %s AND type = %s",
                    (rating.value, rating.name, user.id, rating.type),
                )
        db.commit()

    @classmethod
    def remove_rating_for_user(cls, user: "User", rating: Self):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM rating WHERE user_id = %s AND id = %s",
                (user.id, rating.id),
            )
        db.commit()
