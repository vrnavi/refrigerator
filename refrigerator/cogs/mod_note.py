import revolt
from revolt.ext import commands
from helpers.checks import check_if_staff, check_only_server
from helpers.userlogs import userlog


class ModNote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["addnote"])
    async def note(self, ctx: commands.Context, target: commands.MemberConverter, *, note: str = ""):
        """[S] Adds a note to a user."""
        userlog(ctx.server.id, target.id, ctx.author, note, "notes")
        await ctx.send("Noted.")


def setup(bot):
    return ModNote(bot)
