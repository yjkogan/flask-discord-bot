import sqlite3

from ..ratings import RatingCalculator

from flaskr.db import get_db


class ArtistExistsException(Exception):
    pass


class Artist:
    def __init__(self, name, rating, user_id):
        self.name = name
        self.rating = rating
        self.user_id = user_id

    @classmethod
    def create_from_db_row(cls, row):
        return cls(name=row["name"], rating=row["rating"], user_id=row["user_id"])

    @classmethod
    def get_or_create_artist(cls, user, artist_name):
        artist = cls.get_by_name_for_user(user=user, artist_name=artist_name)
        if artist is None:
            artist = cls.create_artist(user, artist_name)
        return artist

    @classmethod
    def get_artists_for_user(cls, user):
        artists = (
            get_db()
            .execute(
                "SELECT * FROM artist WHERE user_id = ? ORDER BY rating ASC",
                (user.id,),
            )
            .fetchall()
        )
        return [cls.create_from_db_row(artist) for artist in artists]

    @classmethod
    def create_artist(cls, user, artist_name):
        db = get_db()
        try:
            db.execute(
                "INSERT INTO artist (user_id, name) VALUES (?, ?)",
                (user.id, artist_name),
            )
            db.commit()
            return cls(name=artist_name, rating=None, user_id=user.id)

        except sqlite3.IntegrityError as e:
            raise ArtistExistsException(e)

    @classmethod
    def get_by_name_for_user(cls, user, artist_name):
        artist = (
            get_db()
            .execute(
                "SELECT * FROM artist WHERE user_id = ? AND name = ?",
                (user.id, artist_name),
            )
            .fetchone()
        )
        if artist is None:
            return None
        return cls.create_from_db_row(artist)

    @classmethod
    def update_all_with_new_ratings(cls, user, new_rateables):
        db = get_db()
        for rateable in new_rateables:
            db.execute(
                'UPDATE artist'
                ' SET rating = ?'
                ' WHERE name = ? AND user_id = ?',
                (rateable.rating, rateable.name, user.id)
            )
        db.commit()
        

    def begin_rating(self, artists_for_user):
        rating_calculator = RatingCalculator(self, artists_for_user)

        return rating_calculator
    
    def continue_rating(self, comparison):
        rating_calculator = RatingCalculator.find_for_item(self)
        if rating_calculator is None:
            return None
        rating_calculator.add_comparison(comparison)
        return rating_calculator
