from enum import Enum, verify, UNIQUE
import click
from .discord.commands import (
    ApplicationCommandType,
    ApplicationCommandOptionType,
    install_global_commands,
)

from flask import current_app


@verify(UNIQUE)
class BotCommandNames(str, Enum):
    echo = "echo"
    rate_artist = "rate_artist"


TEST_COMMAND = {
    "name": BotCommandNames.echo.name,
    "description": "Respond with whatever was sent",
    "type": ApplicationCommandType.CHAT_INPUT.value,
    "options": [
        {
            "type": ApplicationCommandOptionType.STRING.value,
            "name": "statement",
            "required": True,
            "description": "What to echo back",
        }
    ],
}

RATE_COMMAND = {
    "name": BotCommandNames.rate_artist.name,
    "description": "Rate a musical artist",
    "type": ApplicationCommandType.CHAT_INPUT.value,
    "options": [
        {
            "type": ApplicationCommandOptionType.STRING.value,
            "name": "song_artist",
            "required": True,
            "description": "The artist of the song",
        }
    ],
}

ALL_COMMANDS = [TEST_COMMAND, RATE_COMMAND]


def init_app(app):
    app.cli.add_command(create_commands_command)


@click.command("create-commands")
def create_commands_command():
    install_global_commands(appId=current_app.config["APP_ID"], commands=ALL_COMMANDS)
    click.echo("Installed commands.")
