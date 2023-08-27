import random
import revolt
from revolt.ext import commands
import math
import platform
from helpers.checks import check_if_staff
import datetime
from helpers.placeholders import random_bot_msg


class Meme(commands.Cog):
    """
    Meme commands.
    """

    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot

    @commands.check(check_if_staff)
    @commands.command(name="warm")
    async def warm_member(self, ctx: commands.Context, user: commands.MemberConverter):
        """Warms a user :3"""
        celsius = random.randint(15, 100)
        fahrenheit = self.bot.c_to_f(celsius)
        kelvin = self.bot.c_to_k(celsius)
        await ctx.send(
            f"{user.mention} warmed."
            f" User is now {celsius}°C "
            f"({round(fahrenheit)}°F, {round(kelvin, 2)}K)."
        )

    @commands.check(check_if_staff)
    @commands.command(name="chill", aliases=["cold"])
    async def chill_member(self, ctx: commands.Context, user: commands.MemberConverter):
        """Chills a user >:3"""
        celsius = random.randint(-50, 15)
        fahrenheit = self.bot.c_to_f(celsius)
        kelvin = self.bot.c_to_k(celsius)
        await ctx.send(
            f"{user.mention} chilled."
            f" User is now {celsius}°C "
            f"({round(fahrenheit)}°F, {round(kelvin, 2)}K)."
        )

    @commands.command(aliases=["thank"])
    async def gild(self, ctx: commands.Context, user: commands.MemberConverter):
        """Gives a star to a user"""
        await ctx.send(f"{user.display_name} gets a :star:, yay!")

    @commands.command()
    async def btwiuse(self, ctx: commands.Context):
        """btw i use arch"""
        uname = platform.uname()
        await ctx.send(
            f"BTW I use {platform.python_implementation()} "
            f"{platform.python_version()} on {uname.system} "
            f"{uname.release}"
        )

    @commands.command()
    async def yahaha(self, ctx: commands.Context):
        """secret command"""
        await ctx.send(f"🍂 you found me 🍂")

    @commands.command()
    async def peng(self, ctx: commands.Context):
        """heck tomger"""
        await ctx.send(f"🐧")

    @commands.command(aliases=["outstanding"])
    async def outstandingmove(self, ctx: commands.Context):
        """Posts the outstanding move meme"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments"
            "/371047036348268545/528413677007929344"
            "/image0-5.jpg"
        )

    @commands.command()
    async def bones(self, ctx: commands.Context):
        await ctx.send("https://cdn.discordapp.com/emojis/443501365843591169.png?v=1")

    @commands.command()
    async def headpat(self, ctx: commands.Context):
        await ctx.send("https://cdn.discordapp.com/emojis/465650811909701642.png?v=1")

    @commands.check(check_if_staff)
    @commands.command(name="bam")
    async def bam_member(self, ctx: commands.Context, target: revolt.Member):
        """Bams a user owo"""
        if target.id == self.bot.user.id:
            return await ctx.send(random_bot_msg(ctx.author.name))

        await ctx.send(f"{ctx.author.name} is ̶n͢ow b̕&̡.̷ 👍̡")

    @commands.command()
    async def memebercount(self, ctx: commands.Context):
        """Checks memeber count, as requested by dvdfreitag"""
        await ctx.send("Fuck, IDK, dude.")

    @commands.command(
        aliases=[
            "yotld",
            "yold",
            "yoltd",
            "yearoflinuxondesktop",
            "yearoflinuxonthedesktop",
        ],
    )
    async def yearoflinux(self, ctx: commands.Context):
        """Shows the year of Linux on the desktop"""
        await ctx.send(
            f"{datetime.datetime.now().year} is the year of Linux on the Desktop"
        )


def setup(bot):
    return Meme(bot)
