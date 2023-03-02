import time
import config
import discord
from discord.ext import commands
from discord.ext.commands import Cog


class Basic(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """[U] Says hello!"""
        await ctx.send(f"Hello {ctx.author.mention}! Have you drank your Soylent Green today?")
        
    @commands.command()
    async def hug(self, ctx):
        """[U] Gives you a hug."""
        await ctx.send(f"I am incapable of hugs, but... \*hugs*")

    @commands.command()
    async def kill(self, ctx, the_text: str):
        """[U] Kills someone."""
        await ctx.send(
            f"{the_text} got stuck in the Dishwasher."
        )

    @commands.command()
    async def avy(self, ctx, target):
        """[U] Gets an avy."""
        # In the case of IDs.
        try:
            target_id = int(target)
            avy = self.bot.get_user(target_id).display_avatar.url
        # In the case of mentions.
        except ValueError:
            avy = self.bot.get_user(target[2:-1]).display_avatar.url
        await ctx.send(content=avy)

    @commands.command()
    async def install(self, ctx):
        """[U] Teaches you how to install a Dishwasher."""
        await ctx.send(
            f"Here's how to install a dishwasher:\n<https://www.whirlpool.com/blog/kitchen/how-to-install-a-dishwasher.html>\n\nWhile you're at it, consider protecting your dishwasher:\n<https://www.2-10.com/homeowners-warranty/dishwasher/>\n\nRemember, the more time you spend with your dishwasher instead of the kitchen sink, __the better__."
        )

    @commands.cooldown(1, 10, type=commands.BucketType.user)
    @commands.command(name="hex")
    async def _hex(self, ctx, num: int):
        """[U] Converts base 10 to 16."""
        hex_val = hex(num).upper().replace("0X", "0x")
        await ctx.send(f"{ctx.author.mention}: {hex_val}")

    @commands.cooldown(1, 10, type=commands.BucketType.user)
    @commands.command(name="dec")
    async def _dec(self, ctx, num):
        """[U] Converts base 16 to 10."""
        await ctx.send(f"{ctx.author.mention}: {int(num, 16)}")

    @commands.guild_only()
    @commands.command()
    async def membercount(self, ctx):
        """[U] Prints the member count of the server."""
        await ctx.send(f"{ctx.guild.name} has {ctx.guild.member_count} members!")

    @commands.command(hidden=True)
    async def about(self, ctx):
        """[U] Shows a quick embed with bot info."""
        embed = discord.Embed(
            title="Dishwasher", url=config.source_url, description=config.embed_desc
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["commands"])
    async def help(self, ctx):
        """Posts a help command."""
        await ctx.send("[Press F1 For] HELP\nhttps://os.whistler.page/F1")

    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        """[U] Shows ping values to discord.

        RTT = Round-trip time, time taken to send a message to discord
        GW = Gateway Ping"""
        before = time.monotonic()
        tmp = await ctx.send("Calculating ping...")
        after = time.monotonic()
        rtt_ms = (after - before) * 1000
        gw_ms = self.bot.latency * 1000

        message_text = f":ping_pong:\nrtt: `{rtt_ms:.1f}ms`\ngw: `{gw_ms:.1f}ms`"
        self.bot.log.info(message_text)
        await tmp.edit(content=message_text)


async def setup(bot):
    await bot.add_cog(Basic(bot))
