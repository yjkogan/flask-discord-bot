# import sqlite3
import psycopg2
from psycopg2.extras import LoggingConnection, RealDictCursor

import click
from flask import current_app, g

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def get_db():
    if 'db_connection' not in g:
        db_settings =  {
            "dbname": current_app.config['DB_NAME'],
            "user": current_app.config['DB_USER'],
            "password": current_app.config['DB_PASSWORD'],
            "host": current_app.config['DB_HOST'],
        }
        g.db_connection = psycopg2.connect(connection_factory=LoggingConnection, cursor_factory=RealDictCursor, **db_settings)
        g.db_connection.initialize(current_app.logger)

    return g.db_connection


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    with current_app.open_resource('schema.sql') as f:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(f.read().decode('utf8'))
        conn.commit()


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')
