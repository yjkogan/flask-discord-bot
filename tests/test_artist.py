from flaskr.models.user import User
from flaskr.models.artist import Artist
from flaskr.ratings import Rateable

def test_create_artist(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        artist_name = "test_artist"
        artist = Artist.create_artist(user, artist_name)
        assert artist.name == artist_name
        assert artist.rating is None
        assert artist.user_id == user.id

        other_artist_name = "other_test_artist"
        other_artist = Artist.create_artist(user, other_artist_name, 100.0)
        assert other_artist.name == other_artist_name
        assert other_artist.rating == 100.0
        assert other_artist.user_id == user.id

def test_get_or_create_artist(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        artist_name = "test_artist"
        artist = Artist.get_or_create_artist(user, artist_name)
        assert artist.name == artist_name
        same_artist_hopefully = Artist.get_or_create_artist(user, artist_name)
        assert same_artist_hopefully.id == artist.id

def test_get_by_name_for_user(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        artist_name = "test_artist"
        artist = Artist.create_artist(user, artist_name)
        assert artist.name == artist_name
        same_artist_hopefully = Artist.get_by_name_for_user(user, artist_name)
        assert same_artist_hopefully.id == artist.id

def test_get_artists(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)

        artists = Artist.get_artists_for_user(user)
        assert artists is not None
        assert len(artists) == 0

        Artist.create_artist(user, "test_artist", 100.0)
        Artist.create_artist(user, "other_artist", 99.0)
        Artist.create_artist(user, "third_artist", 10.0)

        artists = Artist.get_artists_for_user(user)
        assert artists is not None
        assert len(artists) == 3
        assert artists[0].name == "third_artist"
        assert artists[1].name == "other_artist"
        assert artists[2].name == "test_artist"

def test_update_all_with_new_ratings(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)

        a1 = "test_artist"
        a2 = "other_artist"
        a3 = "third_artist"
        Artist.create_artist(user, a1, 100.0)
        Artist.create_artist(user, a2, 99.0)
        Artist.create_artist(user, a3, 10.0)
        artists = Artist.get_artists_for_user(user)
        assert len(artists) == 3

        new_rateables = [
            Rateable(name=a1, rating=15.0),
            Rateable(name=a2, rating=30.0),
            Rateable(name=a3, rating=70.0),
        ]
        Artist.update_all_with_new_ratings(user, new_rateables=new_rateables)
        assert Artist.get_by_name_for_user(user, a1).rating == 15.0
        assert Artist.get_by_name_for_user(user, a2).rating == 30.0
        assert Artist.get_by_name_for_user(user, a3).rating == 70.0
