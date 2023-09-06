import random
from flaskr.models.user import User

def test_create_user(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)
        assert user.username == username

def test_get_or_create_for_discord_user(app):
    with app.app_context():
        test_discord_user = { "username": "trogdor", "id": random.randint(1000, 10000)}
        user = User.get_or_create_for_discord_user(test_discord_user)
        assert user.username == test_discord_user["username"]
        assert user.id is not None
        same_user_hopefully = User.get_or_create_for_discord_user(test_discord_user)
        assert user.id == same_user_hopefully.id

def test_get_by(app):
    with app.app_context():
        username = "test"
        user = User.create_user(username)

        assert username == User.get_by_username(username).username
        assert username == User.get_by_id(user.id).username
