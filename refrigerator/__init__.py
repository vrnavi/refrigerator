import os
import sys
import logging
import logging.handlers
import asyncio
import aiohttp
import config
import random
import voltage
import datetime
import importlib
import traceback
from voltage.ext import commands
from helpers.userdata import get_userprefix

# TODO: check __name__ for __main__ nerd

stdout_handler = logging.StreamHandler(sys.stdout)
log_format = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
stdout_handler.setFormatter(log_format)
log = logging.getLogger("discord")
log.setLevel(logging.INFO)
log.addHandler(stdout_handler)


async def get_prefix(message: voltage.Message, bot: commands.CommandsClient):
    return config.prefixes + get_userprefix(message.author.id)


data = {
    "wanted_jsons": [
        "data/dishtimers.json",
        "data/userdata.json",
    ],
    "server_data": "data/servers",
    "bot_data": "data/bot",
    "all_data": "data",
    "aiosession": None,
    "log_channel": None,
    "start_timestamp": None,
}

bot = commands.CommandsClient(prefix=get_prefix)


@bot.listen("ready")
async def on_ready():
    data["aiosession"] = aiohttp.ClientSession()
    data["log_channel"] = bot.get_channel(config.bot_logchannel)
    data["start_timestamp"] = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    )

    # Send "Dishwasher has started! x has y members!"
    guild = data["log_channel"].server
    msg = (
        f"**{bot.user.name} is now `🟢 ONLINE`.**\n"
        f"`{guild.name}` has `{len(guild.members)}` members."
    )

    await data["log_channel"].send(msg)


@bot.listen("on_message")
async def on_message(message: voltage.Message):
    await bot.wait_for("ready")
    # Insert botban stuff here.
    if message.author.bot:
        return


if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("data/servers"):
    os.makedirs("data/servers")

for wanted_json in data["wanted_jsons"]:
    if not os.path.exists(wanted_json):
        with open(wanted_json, "w") as f:
            f.write("{}")


def main():
    # i've only ported these two so just these for now
    for cog in ["cogs.usertime", "cogs.prefixes", "cogs.admin"]:
        try:
            bot.add_extension(cog, data)
        except:
            log.exception(f"Failed to load cog {cog}.")

    bot.run(config.token)


if __name__ == "__main__":
    main()
