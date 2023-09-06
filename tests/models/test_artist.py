from flaskr.models.user import User
from flaskr.models.rating import Rating

def test_create_rating(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.create_rating(user, rating_name)
        assert rating.name == rating_name
        assert rating.rating is None
        assert rating.user_id == user.id

        other_rating_name = "other_test_rating"
        other_rating = Rating.create_rating(user, other_rating_name, 100.0)
        assert other_rating.name == other_rating_name
        assert other_rating.rating == 100.0
        assert other_rating.user_id == user.id

def test_get_or_create_rating(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.get_or_create_rating(user, rating_name)
        assert rating.name == rating_name
        same_rating_hopefully = Rating.get_or_create_rating(user, rating_name)
        assert same_rating_hopefully.id == rating.id

def test_get_by_id_for_user(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.create_rating(user, rating_name)
        assert rating.name == rating_name
        same_rating_hopefully = Rating.get_by_id_for_user(user, rating.id)
        assert same_rating_hopefully.id == rating.id

def test_get_by_name_for_user(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        rating_name = "test_rating"
        rating = Rating.create_rating(user, rating_name)
        assert rating.name == rating_name
        same_rating_hopefully = Rating.get_by_name_for_user(user, rating_name)
        assert same_rating_hopefully.id == rating.id

def test_get_ratings(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)

        ratings = Rating.get_ratings_for_user(user)
        assert ratings is not None
        assert len(ratings) == 0

        Rating.create_rating(user, "test_rating", 100.0)
        Rating.create_rating(user, "other_rating", 99.0)
        Rating.create_rating(user, "third_rating", 10.0)

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

        a1 = Rating.create_rating(user, "test_rating", 100.0)
        a2 = Rating.create_rating(user, "other_rating", 99.0)
        a3 = Rating.create_rating(user, "third_rating", 10.0)
        ratings = Rating.get_ratings_for_user(user)
        assert len(ratings) == 3

        new_rateables = [
            Rateable(id=a1.id, name=a1.name, rating=15.0),
            Rateable(id=a2.id, name=a2.name, rating=30.0),
            Rateable(id=a3.id, name=a3.name, rating=70.0),
        ]
        Rating.update_all_with_new_ratings(user, new_rateables=new_rateables)
        assert Rating.get_by_name_for_user(user, a1.name).rating == 15.0
        assert Rating.get_by_name_for_user(user, a2.name).rating == 30.0
        assert Rating.get_by_name_for_user(user, a3.name).rating == 70.0
