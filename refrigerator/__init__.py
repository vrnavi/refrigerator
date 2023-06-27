import os
import sys
import logging
import logging.handlers
import asyncio
import aiohttp
import config
import random
import datetime
import importlib
import traceback
import revolt
from revolt.ext import commands
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


class Client(commands.CommandsClient):
    async def get_prefix(self, message: revolt.Message):
        return config.prefixes + get_userprefix(message.author.id)

    async def bot_check(self, ctx: commands.Context):
        return ctx.message.author.bot is False

    async def on_ready(self):
        data["aiosession"] = aiohttp.ClientSession()
        data["log_channel"] = self.get_channel(config.bot_logchannel)
        data["start_timestamp"] = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc
        )

        # Send "Dishwasher has started! x has y members!"
        guild = data["log_channel"].server
        msg = (
            f"**{self.user.name} is now `🟢 ONLINE`.**\n"
            f"`{guild.name}` has `{len(guild.members)}` members."
        )

        await data["log_channel"].send(msg)


if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("data/servers"):
    os.makedirs("data/servers")

for wanted_json in data["wanted_jsons"]:
    if not os.path.exists(wanted_json):
        with open(wanted_json, "w") as f:
            f.write("{}")


async def main():
    async with revolt.utils.client_session() as session:
        bot = Client(session, config.token)
        # i've only ported these two so just these for now
        for cog in ["cogs.usertime", "cogs.prefixes", "cogs.admin"]:
            try:
                target = importlib.import_module(cog)
                if not target:
                    raise Exception()

                bot.add_cog(target.setup(bot, data))
            except:
                log.exception(f"Failed to load cog {cog}.")

        await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
