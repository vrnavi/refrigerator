import discord
from discord.ext.commands import Cog
import matplotlib.pyplot as plt
import os
import shutil


class Joininfo(Cog):
    """
    A cog that displays joining information.
    """

    def __init__(self, bot):
        self.bot = bot
        self.caching.start()

    def cog_unload(self):
        self.caching.cancel()
        shutil.rmtree("data/joingraphs")

    @commands.guild_only()
    @commands.command()
    async def joingraph(self, ctx):
        """[U] Shows the graph of users that joined."""
        await ctx.reply(
            file=discord.File(f"data/joingraphs/{ctx.guild.id}-joingraph.png"),
            mention_author=False,
        )

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

    @tasks.loop(hours=1)
    async def caching(self):
        await self.bot.wait_until_ready()
        if not os.path.exists("data/joingraphs"):
            os.makedirs("data/joingraphs")

        for g in self.bot.guilds:
            rawjoins = [m.joined_at.date() for m in g.members]
            joindates = sorted(list(dict.fromkeys(rawjoins)))
            joincounts = []
            for i, d in enumerate(joindates):
                if i != 0:
                    joincounts.append(joincounts[i - 1] + rawjoins.count(d))
                else:
                    joincounts.append(rawjoins.count(d))
            plt.plot(joindates, joincounts)
            plt.savefig(f"data/joingraphs/{g.id}-joingraph.png", bbox_inches="tight")
            plt.close()


async def setup(bot):
    await bot.add_cog(Reply(bot))
