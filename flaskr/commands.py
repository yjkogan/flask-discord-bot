from enum import Enum
import click
from .discord.commands import (
    ApplicationCommandType,
    ApplicationCommandOptionType,
    install_global_commands,
)

from flask import current_app


class BotCommandNames(str, Enum):
    echo = "echo"
    rate = "rate"

class RateSubCommandNames(str, Enum):
    add_rating = "add_rating"
    remove_rating = "remove_rating"
    list_ratings = "list_ratings"
    list_types = "list_types"


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

ITEM_TYPE_OPTION = {
    "name": "item_type",
    "description": "The type of the item to rate",
    "required": True,
    "type": ApplicationCommandOptionType.STRING.value,
}

RATE_COMMAND = {
    "name": BotCommandNames.rate.name,
    "description": "Rate something and compare it against your other ratings",
    "type": ApplicationCommandType.CHAT_INPUT.value,
    "options": [
        {
            "name": RateSubCommandNames.add_rating.name,
            "description": "Add to your ratings",
            "type": ApplicationCommandOptionType.SUB_COMMAND.value,
            "options": [
                ITEM_TYPE_OPTION,
                {
                    "name": "item_name",
                    "description": "The name of the item to rate",
                    "required": True,
                    "type": ApplicationCommandOptionType.STRING.value,
                },
            ],
        },
        {
            "name": RateSubCommandNames.remove_rating.name,
            "description": "Remove a rating",
            "type": ApplicationCommandOptionType.SUB_COMMAND.value,
            "options": [
                ITEM_TYPE_OPTION,
                {
                    "name": "item_name",
                    "description": "The name of the item to remove",
                    "required": True,
                    "type": ApplicationCommandOptionType.STRING.value,
                },
            ],
        },
        {
            "name": RateSubCommandNames.list_ratings.name,
            "description": "List your ratings",
            "type": ApplicationCommandOptionType.SUB_COMMAND.value,
            "options": [ITEM_TYPE_OPTION],
        },
        {
            "name": RateSubCommandNames.list_types.name,
            "description": "List your rating types",
            "type": ApplicationCommandOptionType.SUB_COMMAND.value,
        },
    ],
}

ALL_COMMANDS = [TEST_COMMAND, RATE_COMMAND]


def init_app(app):
    app.cli.add_command(create_commands_command)


@click.command("create-commands")
def create_commands_command():
    install_global_commands(appId=current_app.config["APP_ID"], commands=ALL_COMMANDS)
    click.echo("Installed commands.")
