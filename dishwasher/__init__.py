import os
import sys
import logging
import logging.handlers
import asyncio
import aiohttp
import config
import random
import discord
import datetime
from discord.ext import commands

# TODO: check __name__ for __main__ nerd

stdout_handler = logging.StreamHandler(sys.stdout)
log_format = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
stdout_handler.setFormatter(log_format)
log = logging.getLogger("discord")
log.setLevel(logging.INFO)
log.addHandler(stdout_handler)


def get_prefix(bot, message):
    prefixes = config.prefixes

    return commands.when_mentioned_or(*prefixes)(bot, message)


wanted_jsons = [
    "data/restrictions.json",
    "data/dishtimers.json",
    "data/userlog.json",
    "data/invites.json",
]

intents = discord.Intents.all()
intents.typing = False

bot = commands.Bot(
    command_prefix=get_prefix, description=config.bot_description, intents=intents
)
bot.help_command = None
bot.log = log
bot.config = config
bot.wanted_jsons = wanted_jsons


@bot.event
async def on_ready():
    bot.aiosession = aiohttp.ClientSession()
    bot.app_info = await bot.application_info()
    bot.botlog_channel = bot.get_channel(config.botlog_channel)

    log.info(
        f"\nLogged in as: {bot.user.name} - "
        f"{bot.user.id}\ndpy version: {discord.__version__}\n"
    )

    bot.session = aiohttp.ClientSession()
    bot.start_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    )


    # Send "Robocop has started! x has y members!"
    guild = bot.botlog_channel.guild
    msg = (
        f"**{bot.user.name} is now ONLINE.**\n"
        f"`{guild.name}` has `{guild.member_count}` members."
    )

    await bot.botlog_channel.send(msg)


@bot.event
async def on_command(ctx):
    log_text = (
        f"{ctx.message.author} ({ctx.message.author.id}): " f'"{ctx.message.content}" '
    )
    if ctx.guild:  # was too long for tertiary if
        log_text += (
            f'in "{ctx.channel.name}" ({ctx.channel.id}) '
            f'on "{ctx.guild.name}" ({ctx.guild.id})'
        )
    else:
        log_text += f"in DMs ({ctx.channel.id})"
    log.info(log_text)


@bot.event
async def on_error(event_method, *args, **kwargs):
    log.error(f"Error on {event_method}: {sys.exc_info()}")


@bot.event
async def on_command_error(ctx, error):
    error_text = str(error)

    err_msg = (
        f'⚠️ **Error:**\nAn error occurred with `{ctx.message.content}` from '
        f'{ctx.message.author} ({ctx.message.author.id}):\n'
        f"```{type(error)}: {error_text}```"
    )

    log.error(err_msg)

    if not isinstance(error, commands.CommandNotFound):
        err_msg = bot.escape_message(err_msg)
        await bot.botlog_channel.send(err_msg)

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send("This command doesn't work in DMs.")
    elif isinstance(error, commands.MissingPermissions):
        roles_needed = "\n- ".join(error.missing_perms)
        return await ctx.send(
            f"**Error: Missing Permissions**\n"
            "You don't have the right permissions to run this command. You need: "
            f"```- {roles_needed}```"
        )
    elif isinstance(error, commands.BotMissingPermissions):
        roles_needed = "\n-".join(error.missing_perms)
        return await ctx.send(
            f"**Error: Missing Permissions**\n"
            "I don't have the right permissions to run this command. "
            "I need: "
            f"```- {roles_needed}```"
        )
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(
            f"**Error: Ratelimited**\n"
            "You're being ratelimited. Try in "
            f"{error.retry_after:.1f} seconds."
        )
    elif isinstance(error, commands.CheckFailure):
        return await ctx.send(
            f"**Error: Check Failure**\n"
            "You might not have the right permissions "
            "to run this command, or you may not be able "
            "to run this command in the current channel."
        )
    elif isinstance(error, commands.CommandInvokeError) and (
        "Cannot send messages to this user" in error_text
    ):
        return await ctx.send(
            f"**Error: DM Failure**\n"
            "I can't DM you. You either have me blocked, or have DMs "
            f"blocked, either globally or for this server.\n"
            "Please resolve that, then "
            "try again."
        )
    elif isinstance(error, commands.CommandNotFound):
        # Nothing to do when command is not found.
        return

    help_text = (
        f"Usage of this command is: ```{ctx.prefix}{ctx.command.name} "
        f"{ctx.command.signature}```\nPlease see `{ctx.prefix}help"
        f"` for more info."
    )

    # Keep a list of commands that involve mentioning users
    # and can involve users leaving/getting banned
    ಠ_ಠ = ["warn", "kick", "ban"]

    if isinstance(error, commands.BadArgument):
        # and if said commands get used, add a specific notice.
        if ctx.command.name in ಠ_ಠ:
            help_text = (
                "This probably means that user left (or already got kicked/banned).\n"
                + help_text
            )

        return await ctx.send(
            f"You gave incorrect arguments. {help_text}"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(
            f"You gave incomplete arguments. {help_text}"
        )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if (message.guild) and (message.guild.id not in config.guild_whitelist):
        return

    # Ignore messages in newcomers channel, unless it's potentially
    # an allowed command
    welcome_allowed = ["reset", "kick", "ban", "warn"]
    if message.channel.id == config.welcome_channel and not any(
        cmd in message.content for cmd in welcome_allowed
    ):
        return

    ctx = await bot.get_context(message)
    await bot.invoke(ctx)


if not os.path.exists("data"):
    os.makedirs("data")

for wanted_json in wanted_jsons:
    if not os.path.exists(wanted_json):
        with open(wanted_json, "w") as f:
            f.write("{}")
            
async def main():
    async with bot:
        for cog in config.initial_cogs:
            try:
                await bot.load_extension(cog)
            except:
                log.exception(f"Failed to load cog {cog}.")
        await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
