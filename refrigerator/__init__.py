import os
import sys
import logging
import logging.handlers
import math
import asyncio
import aiohttp
import time
import datetime
import parsedatetime
import importlib
from typing import Dict, List, Any
import revolt
from revolt.ext import commands
from revolt.ext.commands.context import Context
from helpers.messageutils import message_to_url
import helpers.errors

import config
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


class Refrigerator(commands.CommandsClient, revolt.Client):
    log = log
    data: Dict[str, Any] = data
    sniped: dict[str, revolt.Message] = {}
    snipped: dict[str, tuple[revolt.Message, revolt.Message]] = {}
    on_message_listeners = []
    on_reaction_add_listeners = []

    async def on_command_error(self, ctx: Context, error: Exception) -> None:
        prefix = ctx.message.content.split()[0]
        # We don't want to log commands that don't exist.
        if isinstance(error, commands.errors.CommandNotFound):
            return

        log.error(
            f"An error occurred with `{ctx.message.content}` from "
            f"{ctx.message.author} ({ctx.message.author.id}):\n"
            f"{type(error)}: {error}"
        )

        guildmsg = (
            f"**Guild:** {ctx.server.name}\n**Channel:** {ctx.channel.name}\n**Link:** [Jump]({message_to_url(ctx.message)})\n"
            if ctx.channel.channel_type == revolt.ChannelType.text_channel
            else ""
        )
        err_log_embed = revolt.SendableEmbed(
            title="⚠️ Command Error",
            description=(
                f"An error occurred...\n"
                f"**Command:** `{ctx.message.content}`\n"
                f"**User:** {ctx.author.original_name}#{ctx.author.discriminator} ({ctx.message.author.id})\n"
                f"{guildmsg}"
                f"```{type(error)}: {error}```"
            )
        )

        for m in config.bot_managers:
            channel_dict: revolt.DMChannel = await self.http.open_dm(m)
            channel = await self.fetch_channel(channel_dict["_id"])
            await channel.send(embed=err_log_embed)

        help_text = (
            f"Usage of this command is:\n```{prefix} {ctx.invoked_with} {ctx.command.name} "
            f"{ctx.command.signature}```\nPlease see `{prefix} help"
            f"` for more info."
        )

        if isinstance(error, RuntimeError):
            return await ctx.send(f"You gave incomplete arguments. {help_text}")
        elif isinstance(error, LookupError):
            return await ctx.send("The members or channels provided in your command could not be found.")
        elif isinstance(error, commands.errors.ServerOnly):
            return await ctx.send("This command can only be used in a server.")
        elif isinstance(error, commands.errors.InvalidLiteralArgument) or isinstance(error, commands.errors.BadBoolArgument) or isinstance(error, ValueError):
            return await ctx.send(f"You gave invalid arguments. {help_text}")
        elif isinstance(error, helpers.errors.InsufficientBotPermissionsError):
            return await ctx.send(
                f"**Error: Missing Permissions**\n"
                "I don't have the right permissions to run this command. "
                "I need: "
                f"```- {error.permissions}```"
            )
        elif isinstance(error, helpers.errors.NotBotManagerError):
            return await ctx.send("You must be a bot manager to use this command.")
        elif isinstance(error, helpers.errors.NotStaffError):
            return await ctx.send("You must be a staff member of this server to use this command.")
        elif isinstance(error, commands.errors.CheckError):
            return await ctx.send(
                f"**Error: Check Failure**\n"
                "You might not have the right permissions "
                "to run this command, or you may not be able "
                "to run this command in the current channel."
            )


    async def get_prefix(self, message: revolt.Message):
        return config.prefixes + get_userprefix(message.author.id)

    async def bot_check(self, ctx: commands.Context):
        return ctx.message.author.bot is False

    def parse_time(self, delta_str):
        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(delta_str)
        res_timestamp = math.floor(time.mktime(time_struct))
        return res_timestamp

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
            presence=revolt.PresenceType.online, text="Take THAT, Discord."
        )

    async def on_server_join(self, server: revolt.Server):
        msgs: List[revolt.Message] = []
        for m in config.bot_managers:
            manager = self.get_user(m)
            dm = await self.http.open_dm(manager.id)
            channel: revolt.DMChannel = self.get_channel(dm["_id"])
            msg = await channel.send(
                f"### {self.user.mention} joined `{server.name}` with `{len(server.members)}` members.\n"
                "Check the checkmark within an hour to leave."
            )
            await msg.add_reaction("✅")
            msgs.append(msg)

        await asyncio.sleep(1.0)

        def check(msg: revolt.Message, user: revolt.User, react: str):
            return (
                user.id in config.bot_managers
                and react == "✅"
                and type(msg.channel) == revolt.DMChannel
            )

        try:
            await self.wait_for("reaction_add", timeout=600.0, check=check)
        except asyncio.TimeoutError:
            pass
        else:
            await server.leave_server()
            for m in msgs:
                await m.edit(content=f"{m.content}\n\n(I have left this guild.)")

    async def on_message_delete(self, message: revolt.Message):
        if message.author.bot or isinstance(message.channel, revolt.DMChannel):
            return

        self.sniped[message.channel.id] = message

    # requires that you install revolt.py from the github repo for this to work.
    # python3 -m pip install git+https://github.com/revoltchat/revolt.py
    async def on_message_update(self, before: revolt.Message, after: revolt.Message):
        if before.author.bot or isinstance(before.channel, revolt.DMChannel):
            return

        self.snipped[before.channel.id] = (before, after)

    async def on_message(self, message: revolt.Message):
        if message.author.bot:
            return

        await self.process_commands(message)

        for func in self.on_message_listeners:
            await func(self, message)

    async def on_reaction_add(
        self, message: revolt.Message, user: revolt.User, emoji_id: str
    ):
        for func in self.on_reaction_add_listeners:
            await func(self, message, user, emoji_id)


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
            "cogs.admin",
            "cogs.basic",
            "cogs.prefixes",
            "cogs.usertime",
            "cogs.remind",
            "cogs.oneshot",
            "cogs.namecheck",
            "cogs.mod_userlog",
            "cogs.mod_archive",
            "cogs.explains",
            "cogs.messagescan",
            "cogs.sv_config",
            "cogs.mod"
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
