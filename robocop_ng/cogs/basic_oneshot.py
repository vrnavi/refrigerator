import config
from discord.ext import commands
from discord.ext.commands import Cog


class BasicOneShot(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    async def journalcount(self, ctx):
        """[O] Prints the Strange Journal count of the server."""
        community = ctx.guild.get_role(config.named_roles["journal"])
        await ctx.send(
            f"{ctx.guild.name} has {len(community.members)} Strange Journal members!"
        )
        
    @commands.guild_only()
    @commands.command(hidden=True, aliases=["wistlyr"])
    async def wisty(self, ctx):
        """[U] What does Dishwasher think about wisty?"""
        await ctx.send("HELP! HELP! HELP!")

async def setup(bot):
    await bot.add_cog(BasicOneShot(bot))
