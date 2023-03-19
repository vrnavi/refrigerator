import json
from discord import Member
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.userdata import fill_userdata, set_userdata


class usertime(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timezone(self, ctx: Context, *, timezone: str = None):
        """
        Sets your timezone for use with the 'tf' command.
        Timezones must be supplied the IANA tzdb (i.e. America/Chicago) format.
        """
        
        if timezone == None:
            await ctx.reply(content="You need to enter a timezone. Don't know what yours is? Check this list.\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones\nYou can also use your GMT offset with the following format: `Etc/GMT<offset>`.", mention_author=False)

        if timezone not in available_timezones():
            await ctx.send(
                "Invalid timezone provided. Please provide a timezone in the `America/Chicago` format."
            )
            return

        userdata, uid = fill_userdata(ctx.author.id)
        userdata[uid]["timezone"] = timezone

        set_userdata(json.dumps(userdata))
        await ctx.send(f"Your timezone has been set to `{timezone}`.")

    @commands.command(aliases=["tf"])
    async def timefor(self, ctx: Context, target: Member = None):
        """Send the current time in the invoker's (or mentioned user's) time zone."""
        target_is_invoker = target is None

        userdata, uid = fill_userdata(ctx.author.id if target_is_invoker else target.id)
        if userdata[uid]["timezone"] is False:
            await ctx.send(
                "I have no idea what time it is for you. You can set your timezone with `timezone`."
                if target_is_invoker
                else f"I don't know what time it is for {target.display_name}."
            )
            return

        now = datetime.now(ZoneInfo(userdata[uid]["timezone"]))
        await ctx.send(
            f"{'Your' if target_is_invoker else 'Their'} current time is `{now.strftime('%H:%M, %Y-%m-%d')}`"
        )


async def setup(bot: Bot):
    await bot.add_cog(usertime(bot))
