import os
import sys
import logging
import logging.handlers
import asyncio
import aiohttp
import config
import datetime
import importlib
from typing import Dict, Any
import revolt
from revolt.ext import commands

from helpers.userdata import get_userprefix

# TODO: check __name__ for __main__ nerd

stdout_handler = logging.StreamHandler(sys.stdout)
log_format = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
stdout_handler.setFormatter(log_format)
log = logging.getLogger("revolt")
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


class Refrigerator(commands.CommandsClient):
    log = log
    data: Dict[str, Any] = data

    async def get_prefix(self, message: revolt.Message):
        return config.prefixes + get_userprefix(message.author.id)

    async def bot_check(self, ctx: commands.Context):
        return ctx.message.author.bot is False

    async def slice_message(
        self, text: str, size: int = 2000, prefix: str = "", suffix: str = ""
    ):
        """Slices a message into multiple messages."""
        reply_list = []
        size_wo_fix = size - len(prefix) - len(suffix)
        while len(text) > size_wo_fix:
            reply_list.append(f"{prefix}{text[:size_wo_fix]}{suffix}")
            text = text[size_wo_fix:]
        reply_list.append(f"{prefix}{text}{suffix}")
        return reply_list

    async def async_call_shell(
        self, shell_command: str, inc_stdout=True, inc_stderr=True
    ):
        pipe = asyncio.subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(
            str(shell_command), stdout=pipe, stderr=pipe
        )

        if not (inc_stdout or inc_stderr):
            return "??? you set both stdout and stderr to False????"

        proc_result = await proc.communicate()
        stdout_str = proc_result[0].decode("utf-8").strip()
        stderr_str = proc_result[1].decode("utf-8").strip()

        if inc_stdout and not inc_stderr:
            return stdout_str
        elif inc_stderr and not inc_stdout:
            return stderr_str

        if stdout_str and stderr_str:
            return f"stdout:\n\n{stdout_str}\n\n" f"======\n\nstderr:\n\n{stderr_str}"
        elif stdout_str:
            return f"stdout:\n\n{stdout_str}"
        elif stderr_str:
            return f"stderr:\n\n{stderr_str}"

        return "No output."

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

        log.info(
            f"Bot is Ready as {self.user.name}#{self.user.discriminator} ({self.user.id})"
        )

        await self.edit_status(
            presence=revolt.PresenceType.focus, text="Take THAT, Discord."
        )

    async def on_server_join(self, server: revolt.Server):
        mentions = ", ".join(
            [self.get_user(uid).mention for uid in config.bot_managers]
        )

        channel = self.get_channel(config.bot_logchannel)
        msg: revolt.Message = await channel.send(
            f"### {mentions}\n\n"
            f"### {self.user.mention} joined `{server.name}` with `{len(server.members)}` members.\n"
            "Check the checkmark within an hour to leave."
        )
        await msg.add_reaction("%E2%9C%85")  # :white_check_mark:
        await asyncio.sleep(1.0)

        def check(msg: revolt.Message, user: revolt.User, react: str):
            return bool(user.id in config.bot_managers and react == "✅")

        try:
            await self.wait_for("reaction_add", timeout=600.0, check=check)
        except asyncio.TimeoutError:
            await msg.edit(content=f"{msg.content}\n\n(Interaction timeout.)")
        else:
            await server.leave_server()
            await msg.edit(content=f"{msg.content}\n\n(I have left this guild.)")


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
        bot = Refrigerator(session, config.token)

        # TODO: Port all discord.py-like cogs into revolt.py-like
        ported_cogs = [
            "cogs.prefixes",
            "cogs.usertime",
            "cogs.admin",
            "cogs.basic",
            "cogs.oneshot",
            "cogs.namecheck",
        ]
        for cog in ported_cogs:
            try:
                target = importlib.import_module(cog)
                if not target:
                    raise Exception()
                bot.add_cog(target.setup(bot))
            except:
                log.exception(f"Failed to load cog {cog}.")

        await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
