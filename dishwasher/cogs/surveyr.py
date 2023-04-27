import discord
from discord.ext.commands import Cog
import json
import config
import datetime
from helpers.checks import check_if_staff
from helpers.configs import get_surveyr_config, config_check


class Surveyr(Cog):
    """
    An open source Pollr clone.
    """

    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Surveyr isn't set up for this server."

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(invoke_without_command=True, aliases=["s"])
    async def survey(self, ctx, caseid: int = None):
        """[S] Invokes Surveyr."""
        if not config_check(ctx.guild.id, "surveyr"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        pass


async def setup(bot):
    await bot.add_cog(Surveyr(bot))
