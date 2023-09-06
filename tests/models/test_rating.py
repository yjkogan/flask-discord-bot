from flaskr.models.user import User
from flaskr.models.rating import Rating

def test_create_rating(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.create_rating(user, rating_name, 'artist')
        assert rating.name == rating_name
        assert rating.value is None
        assert rating.user_id == user.id

        other_rating_name = "other_test_rating"
        other_rating = Rating.create_rating(user, other_rating_name, 'artist', 100.0)
        assert other_rating.name == other_rating_name
        assert other_rating.value == 100.0
        assert other_rating.user_id == user.id

def test_get_or_create_rating(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.get_or_create_rating(user, rating_name, 'artist')
        assert rating.name == rating_name
        same_rating_hopefully = Rating.get_or_create_rating(user, rating_name, 'artist')
        assert same_rating_hopefully.id == rating.id

def test_get_by_id_for_user(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.create_rating(user, rating_name, 'artist')
        assert rating.name == rating_name
        same_rating_hopefully = Rating.get_by_id_for_user(user, rating.id)
        assert same_rating_hopefully.id == rating.id

def test_get_by_name_for_user(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.create_rating(user, rating_name, 'artist')
        assert rating.name == rating_name
        same_rating_hopefully = Rating.get_by_name_for_user(user, rating_name, 'artist')
        assert same_rating_hopefully.id == rating.id

def test_get_ratings(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)

        ratings = Rating.get_ratings_for_user(user)
        assert ratings is not None
        assert len(ratings) == 0

        Rating.create_rating(user, "test_rating", 'artist', 100.0)
        Rating.create_rating(user, "other_rating", 'artist', 99.0)
        Rating.create_rating(user, "third_rating", 'artist', 10.0)

        ratings = Rating.get_ratings_for_user(user)
        assert ratings is not None
        assert len(ratings) == 3
        assert ratings[0].name == "third_rating"
        assert ratings[1].name == "other_rating"
        assert ratings[2].name == "test_rating"

def test_update_all_with_new_ratings(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)

        a1 = Rating.create_rating(user, "test_rating", 'artist', 100.0)
        a2 = Rating.create_rating(user, "other_rating", 'artist', 99.0)
        a3 = Rating.create_rating(user, "third_rating", 'artist', 10.0)
        ratings = Rating.get_ratings_for_user(user)
        assert len(ratings) == 3

        new_ratings = [
            Rating(id=a1.id, name=a1.name, value=15.0, type='artist', user_id=user.id),
            Rating(id=a2.id, name=a2.name, value=30.0, type='artist', user_id=user.id),
            Rating(id=a3.id, name=a3.name, value=70.0, type='artist', user_id=user.id),
        ]
        Rating.update_all_with_new_ratings(user, new_ratings=new_ratings)
        assert Rating.get_by_name_for_user(user, a1.name, 'artist').value == 15.0
        assert Rating.get_by_name_for_user(user, a2.name, 'artist').value == 30.0
        assert Rating.get_by_name_for_user(user, a3.name, 'artist').value == 70.0
