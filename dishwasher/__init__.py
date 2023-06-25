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

wanted_jsons = [
    "data/dishtimers.json",
    "data/userdata.json",
]
server_data = "data/servers"
bot_data = "data/bot"
all_data = "data"

bot = commands.CommandsClient(
    prefix=get_prefix
)

# These do not work, as CommandsClient does not have a __dict__ attribute
# which means we can't dynamically shove attributes onto it
# Code that references these will need to be updated

# bot.wanted_jsons = wanted_jsons
# bot.server_data = server_data
# bot.bot_data = bot_data
# bot.all_data = all_data


@bot.listen("ready")
async def on_ready():
    bot.aiosession = aiohttp.ClientSession()
    bot.log_channel = bot.get_channel(config.bot_logchannel)

    bot.session = aiohttp.ClientSession()
    bot.start_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    )

    # Send "Dishwasher has started! x has y members!"
    guild = bot.log_channel.server
    msg = (
        f"**{bot.user.name} is now `🟢 ONLINE`.**\n"
        f"`{guild.name}` has `{len(guild.members)}` members."
    )

    await bot.log_channel.send(msg)


@bot.listen("on_message")
async def on_message(message: voltage.Message):
    await bot.wait_for("ready")
    # Insert botban stuff here.
    if message.author.bot:
        return


if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(server_data):
    os.makedirs(server_data)

for wanted_json in wanted_jsons:
    if not os.path.exists(wanted_json):
        with open(wanted_json, "w") as f:
            f.write("{}")


def main():
    # i've only ported these two so just these for now
    for cog in ['cogs.usertime', 'cogs.prefixes']:
        try:
            target = importlib.import_module(cog)
            if not target:
                raise Exception()

            bot.add_cog(target.setup(bot))
        except:
            log.exception(f"Failed to load cog {cog}.")

    bot.run(config.token)


if __name__ == "__main__":
    main()
