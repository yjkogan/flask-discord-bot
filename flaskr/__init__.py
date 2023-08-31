import os

from flask import Flask
from .config.logging import configure_logger

from . import db
from . import commands
from . import discord_interactions

def create_app(test_config=None):
    configure_logger()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=False)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize Stuff
    db.init_app(app)
    commands.init_app(app)

    # Register routes
    app.register_blueprint(discord_interactions.bp)

    return app
