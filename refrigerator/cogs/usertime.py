import json
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
from revolt.ext import commands

from helpers.userdata import fill_userdata, set_userdata


class CogUsertime(commands.Cog):
    def __init__(self, bot: commands.CommandsClient):
        self.qualified_name = "usertime"
        self.bot = bot

    @commands.command()
    async def timezone(self, ctx: commands.Context, *, timezone: str):
        """
        Sets your timezone for use with the 'tf' command.
        Timezones must be supplied the IANA tzdb (i.e. America/Chicago) format.
        """
        userdata, uid = fill_userdata(ctx.author.id)
        if not timezone:
            await ctx.message.reply(
                content=f"Your timezone is `{'not set' if not userdata[uid]['timezone'] else userdata[uid]['timezone']}`.\n"
                "To change this, enter a timezone. A list of timezones is available here.\n"
                "<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>\n"
                "You can also use your GMT offset with the following format: `Etc/GMT<offset>`.\n"
                "For example, `Etc/GMT+5` for Eastern Time, or UTC-5.",
                mention=False,
            )
            return
        elif timezone not in available_timezones():
            await ctx.message.reply(
                content="Invalid timezone provided. For help, run `timezone` by itself.",
                mention=False,
            )
            return
        else:
            userdata[uid]["timezone"] = timezone
            set_userdata(json.dumps(userdata))
            await ctx.message.reply(
                f"Your timezone has been set to `{timezone}`.", mention=False
            )

    @commands.command(aliases=["tf"])
    async def timefor(
        self,
        ctx: commands.Context,
        target: commands.converters.MemberConverter = None,
        *,
        time: str,
    ):
        """Send the current time in the invoker's (or mentioned user's) time zone."""
        if time and ctx.author.id != target.id:
            # check both *have* timezones
            suserdata, suid = fill_userdata(ctx.author.id)
            tuserdata, tuid = fill_userdata(target.id)
            if not suserdata[suid]["timezone"]:
                await ctx.message.reply(
                    content="I have no idea what time it is for you. You can set your timezone with `timezone`.",
                    mention=False,
                )
                return
            elif not tuserdata[tuid]["timezone"]:
                await ctx.message.reply(
                    content=f"I don't know what time it is for {target.name}.",
                    mention=False,
                )
                return

            parsed_time = self.parse_time(time)

            if not parsed_time:
                await ctx.message.reply(
                    content="Given time is invalid. Try `12AM`, `12 AM`, `12:00 AM`, or `00:00`.",
                    mention=False,
                )
                return

            suser_timezone = ZoneInfo(suserdata[suid]["timezone"])
            tuser_timezone = ZoneInfo(tuserdata[tuid]["timezone"])

            parsed_time = datetime.combine(
                datetime.now(), parsed_time, tzinfo=tuser_timezone
            )
            parsed_time = parsed_time.astimezone(suser_timezone)

            await ctx.message.reply(
                content=f"`{time}` for them is `{parsed_time.strftime('%I:%M %p')}` for you.",
                mention=False,
            )
        else:
            userdata, uid = fill_userdata(ctx.author.id if not target else target.id)
            if not userdata[uid]["timezone"]:
                await ctx.message.reply(
                    content=(
                        "I have no idea what time it is for you. You can set your timezone with `timezone`."
                        if not target
                        else f"I don't know what time it is for {target.name}."
                    ),
                    mention=False,
                )
                return
            now = datetime.now(ZoneInfo(userdata[uid]["timezone"]))
            await ctx.message.reply(
                content=f"{'Your' if not target else 'Their'} current time is `{now.strftime('%H:%M, %Y-%m-%d')}`",
                mention=False,
            )
            return

    def parse_time(self, time_str: str):
        for fmt in ("%I %p", "%I%p", "%I:%M %p", "%H:%M"):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                pass
        return None


def setup(bot: commands.CommandsClient):
    return CogUsertime(bot)
