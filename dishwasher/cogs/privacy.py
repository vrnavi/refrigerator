import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import config
import datetime
import asyncio
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class Privacy(Cog):
    """
    For when you want to be forgotten.
    """

    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Privacy(bot))
