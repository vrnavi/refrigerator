import discord
from discord.ext.commands import Cog
import json
import re
import config
import datetime
from helpers.checks import check_if_staff


class Reply(Cog):
    """
    A cog that stops people from ping replying people who don't want to be.
    """

    def __init__(self, bot):
        self.bot = bot
        self.last_eval_result = None
        self.previous_eval_code = None

    async def handle_message_with_reference(self, message):
        reference_author = message.reference.resolved.author
        if (
            message.author.bot
            or message.guild.id not in config.guild_configs
            or reference_author.get_role(config.guild_configs[message.guild.id]["misc"]["noreply_role"]) is None
            or reference_author.id is message.author.id
            or message.author.get_role(config.guild_configs[message.guild.id]["staff"]["staff_role"]) is not None
        ):
            return

        if reference_author in message.mentions:
            await message.add_reaction("🗞️")
            await message.reply(
                file=discord.File("assets/noreply.png"),
                delete_after=15,
                mention_author=True,
            )

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if message.reference:
            await self.handle_message_with_reference(message)


async def setup(bot):
    await bot.add_cog(Reply(bot))
