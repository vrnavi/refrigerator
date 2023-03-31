import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.userlogs import userlog


class ModNote(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["addnote"])
    async def note(self, ctx, target: discord.User, *, note: str = ""):
        """[S] Adds a note to a user."""
        userlog(target.id, ctx.author, note, "notes", target.name)
        await ctx.send(f"Noted.")


async def setup(bot):
    await bot.add_cog(ModNote(bot))
