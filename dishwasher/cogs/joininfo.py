import discord
from discord.ext.commands import Cog
import matplotlib.pyplot as plt
import os


class Joininfo(Cog):
    """
    A cog that displays joining information.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @commands.command()
    async def joingraph(self, ctx):
        """[U] Shows the graph of users that joined."""
        async with ctx.channel.typing():
            rawjoins = [m.joined_at.date() for m in ctx.guild.members]
            joindates = sorted(list(dict.fromkeys(rawjoins)))
            joincounts = []
            for i, d in enumerate(joindates):
                if i != 0:
                    joincounts.append(joincounts[i - 1] + rawjoins.count(d))
                else:
                    joincounts.append(rawjoins.count(d))
            plt.plot(joindates, joincounts)
            plt.savefig("testfile.png", bbox_inches="tight")
            plt.close()
        await ctx.reply(file=discord.File("testfile.png"), mention_author=False)
        os.remove("testfile.png")

    @commands.guild_only()
    @commands.command(aliases=["joinscore"])
    async def joinorder(self, ctx, joinscore: int = None):
        """[U] Shows the joinorder of a user."""
        members = sorted(ctx.guild.members, key=lambda v: v.joined_at)
        message = ""
        memberidx = joinscore if joinscore else members.index(ctx.author) + 1
        for idx, m in enumerate(members):
            if memberidx - 6 <= idx <= memberidx + 4:
                message = (
                    f"{message}\n`{idx+1}` **{m}**"
                    if memberidx == idx + 1
                    else f"{message}\n`{idx+1}` {m}"
                )
        await ctx.reply(content=message, mention_author=False)


async def setup(bot):
    await bot.add_cog(Reply(bot))
