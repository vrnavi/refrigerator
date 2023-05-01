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

        userdata, uid = fill_userdata(ctx.author.id)
        if timezone == None:
            await ctx.reply(
                content=f"Your timezone is `{'not set' if not userdata[uid]['timezone'] else userdata[uid]['timezone']}`.\n"
                "To change this, enter a timezone. Check the list below if you don't know what yours is.\n"
                "<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>\n"
                "You can also use your GMT offset with the following format: `Etc/GMT<offset>`. For example, `Etc/GMT+5`.",
                mention_author=False,
            )
            return
        elif timezone not in available_timezones():
            await ctx.reply(
                content="Invalid timezone provided. Please provide a timezone in the `America/Chicago` format.\n"
                "If you don't know what yours is, please check the following list.\n"
                "<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>\n"
                "You can also use your GMT offset with the following format: `Etc/GMT<offset>`. For example, `Etc/GMT+5`.",
                mention_author=False,
            )
            return
        else:
            userdata[uid]["timezone"] = timezone
            set_userdata(json.dumps(userdata))
            await ctx.reply(
                f"Your timezone has been set to `{timezone}`.", mention_author=False
            )

    @commands.command(aliases=["tf"])
    async def timefor(self, ctx: Context, target: Member = None):
        """Send the current time in the invoker's (or mentioned user's) time zone."""
        userdata, uid = fill_userdata(ctx.author.id if not target else target.id)
        if not userdata[uid]["timezone"]:
            await ctx.send(
                "I have no idea what time it is for you. You can set your timezone with `timezone`."
                if not target
                else f"I don't know what time it is for {target.display_name}."
            )
            return

        now = datetime.now(ZoneInfo(userdata[uid]["timezone"]))
        await ctx.send(
            f"{'Your' if not target else 'Their'} current time is `{now.strftime('%H:%M, %Y-%m-%d')}`"
        )


async def setup(bot: Bot):
    await bot.add_cog(usertime(bot))
