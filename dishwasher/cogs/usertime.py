import json
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.userdata import fill_userdata, set_userdata

class usertime(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timezone(self, ctx: Context, *, timezone: str):
        """
        Sets your timezone for use with the 'tf' command.
        Timezones must be supplied the IANA tzdb (i.e. America/Chicago) format.
        """
        if (timezone not in available_timezones()):
            await ctx.send("Invalid timezone provided. Please provide a timezone in the `America/Chicago` format.")
            return

        userdata, uid = fill_userdata(ctx.author.id)
        userdata[uid]["timezone"] = timezone

        set_userdata(json.dumps(userdata))
        await ctx.send(f"Your timezone has been set to `{timezone}`.")

    @commands.command(aliases=['tf'])
    async def timefor(self, ctx: Context):
        """[U] Send the current time in the invoker's time zone."""
        userdata, uid = fill_userdata(ctx.author.id)
        if (userdata[uid]["timezone"] is False):
            await ctx.send("I have no idea what time it is for you. You can set your timezone with `timezone`.")
            return

        now = datetime.now(ZoneInfo(userdata[uid]["timezone"]))
        await ctx.send(f"Your current time is `{now.strftime('%H:%M, %Y-%m-%d')}`")

async def setup(bot: Bot):
    await bot.add_cog(usertime(bot))
