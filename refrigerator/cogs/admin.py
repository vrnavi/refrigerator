import importlib
import traceback
import inspect
import re
import datetime
import json
import config
import random
import asyncio
import shutil
import os
import config
import revolt
from revolt.ext import commands

from helpers.checks import check_if_bot_manager
from helpers.sv_config import get_config


class CogAdmin(commands.Cog):
    def __init__(self, bot: commands.CommandsClient, data):
        self.qualified_name = "admin"
        self.bot = bot
        self.data = data
        self.last_eval_result = None
        self.previous_eval_code = None

    @commands.check(check_if_bot_manager)
    @commands.command(name="exit", aliases=["quit", "bye"])
    async def _exit(self, ctx: commands.Context):
        """[O] Shuts down (or restarts) the bot."""
        await ctx.message.reply(
            content=random.choice(config.death_messages), mention=False
        )
        self.bot.log.info(
            f"{ctx.author.original_name}#{ctx.author.discriminator} ({ctx.author.id}) issued shutdown command"
        )
        await self.bot.stop()

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def getdata(self, ctx: commands.Context):
        """[O] Returns data files."""
        shutil.make_archive("data_backup", "zip", self.data["all_data"])
        await ctx.message.reply(
            content="Your current data files...",
            attachments=[revolt.File("data_backup.zip")],
            mention=False,
        )
        os.remove("data_backup.zip")

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def setdata(self, ctx: commands.Context):
        """[O] Replaces data files. This is destructive behavior!"""
        if not ctx.message.attachments:
            await ctx.message.reply(
                content="You need to supply the data files.", mention=False
            )
            return
        with open("data.zip", "wb") as fp:
            await ctx.message.attachments[0].save(fp)
        if os.path.exists("data"):
            shutil.rmtree("data")
        shutil.unpack_archive("data.zip", "data")
        await ctx.message.reply(f"{ctx.server.name}'s data saved.", mention=False)

    @commands.check(check_if_bot_manager)
    @commands.command(aliases=["getserverdata"])
    async def getsdata(self, ctx: commands.Context, server: str = None):
        """[O] Returns server data."""
        if server:
            try:
                server = self.bot.get_server(server)
            except LookupError:
                await ctx.message.reply(
                    "That server is not in bot's servers.",
                    mention=False,
                )
                return
        else:
            server = ctx.server

        try:
            if not os.path.isdir(f"data/servers/{server.id}"):
                raise FileNotFoundError
            shutil.make_archive(
                f"data/{server.id}", "zip", f"{self.data['server_data']}/{server.id}"
            )
            await ctx.message.reply(
                content=f"{server.name}'s data...",
                attachments=[
                    revolt.File(
                        f"data/{server.id}.zip", filename=f"data_{server.id}.zip"
                    )
                ],
                mention=False,
            )
            os.remove(f"data/{server.id}.zip")
        except FileNotFoundError:
            await ctx.message.reply(
                "That server doesn't have any data.",
                mention=False,
            )

    @commands.check(check_if_bot_manager)
    @commands.command(aliases=["setserverdata"])
    async def setsdata(self, ctx: commands.Context, server: str = None):
        """[O] Replaces server data files. This is destructive behavior!"""
        if server:
            try:
                server = self.bot.get_server(server)
            except LookupError:
                await ctx.message.reply(
                    "That server is not in bot's servers.",
                    mention=False,
                )
                return
        else:
            server = ctx.server

        if not ctx.message.attachments:
            await ctx.message.reply("You need to supply the data file.", mention=False)
            return
        with open(f"data/{server.id}.zip", "wb") as fp:
            await ctx.message.attachments[0].save(fp)
        if os.path.exists(f"{self.data['server_data']}/{server.id}"):
            shutil.rmtree(f"{self.data['server_data']}/{server.id}")
        shutil.unpack_archive(
            f"data/{server.id}.zip", f"{self.data['server_data']}/{server.id}"
        )
        await ctx.message.reply(f"{server.name}'s data saved.", mention=False)

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def getlogs(self, ctx: commands.Context):
        """[O] Returns the log file."""
        shutil.copy("logs/dishwasher.log", "logs/upload.log")
        await ctx.message.reply(
            content="The current log file...",
            attachments=[revolt.File("logs/upload.log", filename="dishwasher.log")],
            mention=False,
        )
        os.remove("logs/upload.log")

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def taillogs(self, ctx: commands.Context):
        """[O] Returns the last 10 lines of the log file."""
        shutil.copy("logs/dishwasher.log", "logs/upload.log")
        with open("logs/upload.log", "r+") as f:
            tail = "\n".join(f.read().split("\n")[-10:])
        os.remove("logs/upload.log")
        await ctx.message.reply(
            content=f"The current tailed log file...\n```{tail.replace('```', '')}\n```",
            mention=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command(aliases=["servers"])
    async def guilds(self, ctx: commands.Context):
        """[O] Shows the current guilds I am in."""
        guildmsg = "**I am in the following guilds:**"
        for g in self.bot.servers:
            guildmsg += f"\n- {g.name} (`{g.id}`) with `{len(g.members)}` members."
        await ctx.message.reply(guildmsg, mention=False)

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def permcheck(
        self,
        ctx: commands.Context,
        target: commands.MemberConverter = None,
        channel: commands.ChannelConverter = None,
    ):
        """[O] Shows the permissions."""
        if not ctx.server:
            return
        if not target:
            target = ctx.server.get_member(self.bot.user.id)
        if not channel:
            channel = ctx.channel
        await ctx.message.reply(
            content=f"{target.name}#{target.discriminator}'s permissions for the {channel.mention} channel...\n"
            "```diff\n"
            + "\n".join(
                [
                    f"{'-' if not y else '+'} " + x
                    for x, y in iter(target.get_channel_permissions(ctx.channel))
                ]
            )
            + "\n ```",
            mention=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def threadlock(
        self, ctx: commands.Context, channel: commands.ChannelConverter
    ):
        """[O] Locks all threads in a given channel."""
        await ctx.message.reply("Revolt does not have Threads...", mention=False)
        return
        msg = await ctx.message.reply("Locking threads...", mention=False)
        # Pull old archvied threads from the grave.
        async for t in channel.archived_threads():
            await t.edit(archived=False)
        async for t in channel.archived_threads(private=True, joined=True):
            await t.edit(archived=False)
        # Unsure if needed, but here anyway.
        channel = await ctx.guild.fetch_channel(channel.id)
        # Lock all threads.
        for t in channel.threads:
            await t.edit(locked=True)
            await t.edit(archived=True)
        await msg.edit(content="Done.")

    @commands.check(check_if_bot_manager)
    @commands.command(name="eval")
    async def _eval(self, ctx: commands.Context, *, code: str):
        """[O] Evaluates some code."""
        try:
            code = code.strip("` ")
            env = {
                "bot": self.bot,
                "ctx": ctx,
                "message": ctx.message,
                "server": ctx.server,
                "guild": ctx.server,
                "channel": ctx.message.channel,
                "author": ctx.message.author,
                "config": config,
                # modules
                "revolt": revolt,
                "commands": commands,
                "datetime": datetime,
                "json": json,
                "asyncio": asyncio,
                "random": random,
                "os": os,
                "get_config": get_config,
                # utilities
                "_get": revolt.utils.get,
                # "_find": revolt.utils.find,  # FIXME: revolt.py find util
                # last result
                "_": self.last_eval_result,
                "_p": self.previous_eval_code,
            }
            env.update(globals())

            self.bot.log.info(f"Evaling {repr(code)}:")
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result

            if result is not None:
                self.last_eval_result = result

            self.previous_eval_code = code

            sliced_message = await self.bot.slice_message(
                repr(result), prefix="```", suffix="```"
            )
            for msg in sliced_message:
                await ctx.send(msg)
        except:
            sliced_message = await self.bot.slice_message(
                traceback.format_exc(), prefix="```", suffix="```"
            )
            for msg in sliced_message:
                await ctx.send(msg)

    async def cog_load_actions(self, cog_name):
        # Used for specific cog actions, tore out the verification cog since don't need it.
        pass

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def pull(self, ctx: commands.Context, auto: str = None):
        """[O] Performs a git pull."""
        if auto and auto.lower() in [
            "yes",
            "yeah",
            "yep",
            "true",
            "1",
            "reload",
            "auto",
        ]:
            auto = True
        else:
            auto = False
        tmp = await ctx.message.reply("Pulling...", mention=False)
        git_output = await self.bot.async_call_shell("git pull")
        if len(git_output) > 2000:
            parts = await self.bot.slice_message(
                git_output, prefix="```shell", suffix="```"
            )
            await tmp.edit(content=f"Output too long. Sending in new message...")
            for x in parts:
                await ctx.send(content=x)
        else:
            await tmp.edit(
                content=f"Pull complete. Output:\n```shell\n{git_output}\n```"
            )
        if auto:
            cogs_to_reload = re.findall(r"cogs/([a-z_]*).py[ ]*\|", git_output)
            for cog in cogs_to_reload:
                cog_name = "cogs." + cog
                if cog_name not in config.initial_cogs:
                    continue

                try:
                    self.bot.remove_cog(cog)
                    target = importlib.import_module(f"cogs.{cog}")
                    self.bot.add_cog(target.setup(self.bot))
                    self.bot.log.info(f"Reloaded ext {cog}")
                    await ctx.message.reply(
                        content=f":white_check_mark: `{cog}` successfully reloaded.",
                        mention=False,
                    )
                    await self.cog_load_actions(cog)
                except:
                    await ctx.message.reply(
                        content=f":x: Cog reloading failed, traceback:\n"
                        f"```py\n{traceback.format_exc()}\n```",
                        mention=False,
                    )
                    return

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def load(self, ctx: commands.Context, ext: str):
        """[O] Loads a cog."""
        try:
            target = importlib.import_module(f"cogs.{ext}")
            self.bot.add_cog(target.setup(self.bot))
            await self.cog_load_actions(ext)
        except:
            await ctx.message.reply(
                content=f":x: Cog loading failed, traceback:\n"
                f"```py\n{traceback.format_exc()}\n```",
                mention=False,
            )
            return
        self.bot.log.info(f"Loaded ext {ext}")
        await ctx.message.reply(
            content=f":white_check_mark: `{ext}` successfully loaded.",
            mention=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def unload(self, ctx: commands.Context, ext: str):
        """[O] Unloads a cog."""
        try:
            self.bot.remove_cog(ext)
        except KeyError:
            await ctx.message.reply(
                content=f":x: Cog unloading failed, the cog `{ext}` is not loaded yet.",
                mention=False,
            )
            return
        except Exception:
            await ctx.message.reply(
                content=f":x: Cog unloading failed, traceback:\n"
                f"```py\n{traceback.format_exc()}\n```",
                mention=False,
            )
            return
        self.bot.log.info(f"Unloaded ext {ext}")
        await ctx.message.reply(
            content=f":white_check_mark: `{ext}` successfully unloaded.",
            mention=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def reload(self, ctx: commands.Context, ext: str = "_"):
        """[O] Reloads a cog."""
        if ext == "_":
            ext = self.lastreload
        else:
            self.lastreload = ext

        try:
            self.bot.remove_cog(ext)
            target = importlib.import_module(f"cogs.{ext}")
            self.bot.add_cog(target.setup(self.bot))
            await self.cog_load_actions(ext)
        except KeyError:
            await ctx.message.reply(
                content=f":x: Cog unloading failed, the cog `{ext}` is not loaded yet.",
                mention=False,
            )
            return
        except Exception:
            await ctx.message.reply(
                content=f":x: Cog reloading failed, traceback:\n"
                f"```py\n{traceback.format_exc()}\n```",
                mention=False,
            )
            return

        self.bot.log.info(f"Reloaded ext {ext}")
        await ctx.message.reply(
            content=f":white_check_mark: `{ext}` successfully reloaded.",
            mention=False,
        )


def setup(bot: commands.CommandsClient, data):
    return CogAdmin(bot, data)
