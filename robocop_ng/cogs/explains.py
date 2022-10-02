import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog


class Explains(Cog):
    """
    Commands for easily explaining certain things.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, aliases=["memechannel"])
    async def dumpster(self, ctx):
        """Explains Dumpster."""
        await ctx.send("Dumpster has not, is not, and will never be a core part of this server. It is not coming back.")
        
    @commands.command(hidden=True, aliases=["embeds", "howpostembeds"])
    async def journal(self, ctx):
        """Explains Strange Journal."""
        await ctx.send("To post embeds, react to messages, or speak in voice channels, you need the Strange Journal role.\nTo learn how to get this role, read #controls. **Do __not__ \"spoonfeed\" any user the command for it.**")

async def setup(bot):
    await bot.add_cog(Explains(bot))
