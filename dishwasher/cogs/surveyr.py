import discord
from discord.ext.commands import Cog
import json
import config
import datetime
from helpers.checks import check_if_staff


class Surveyr(Cog):
    """
    An open source Pollr clone.
    """

    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Surveyr(bot))
