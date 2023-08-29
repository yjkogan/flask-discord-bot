import click
from . import discord

from flask import (current_app)

TEST_COMMAND = {
  'name': 'test',
  'description': 'Basic command',
  'type': 1,
}

RATE_COMMAND = {
    'name': 'rate_artist',
    'description': 'Rate a musical artist',
    'type': 1,
    'options': [{
        'type': 3,
        'name': 'song_artist',
        'required': True,
        'description': 'The artist of the song',
    }]
}

ALL_COMMANDS = [TEST_COMMAND, RATE_COMMAND]

def init_app(app):
    app.cli.add_command(create_commands_command)

@click.command('create-commands')
def create_commands_command():
    discord.install_global_commands(appId=current_app.config['APP_ID'], commands=ALL_COMMANDS)
    click.echo('Installed commands.')
