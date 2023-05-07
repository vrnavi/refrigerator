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
    async def timezone(self, ctx, *, timezone: str = None):
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
    async def timefor(self, ctx, target: Member = None, *, time: str = None):
        """Send the current time in the invoker's (or mentioned user's) time zone."""
        if time and target.id != ctx.author.id:
            # check both *have* timezones
            suserdata, suid = fill_userdata(ctx.author.id)
            tuserdata, tuid = fill_userdata(target.id)
            if not suserdata[suid]["timezone"]:
                await ctx.reply(
                    content="I have no idea what time it is for you. You can set your timezone with `timezone`.",
                    mention_author=False,
                )
                return
            elif not tuserdata[tuid]["timezone"]:
                await ctx.reply(
                    content="I don't know what time it is for {target.display_name}.",
                    mention_author=False,
                )
                return

            # horrendous time processing code
            # 12 hour time handler.
            if time[-2:].upper() == "AM" or time[-2:].upper() == "PM":
                # turn 12am into 12 AM if needed
                time = time[:-2] + (" " if " " not in time else "") + time[-2:].upper()
                # turn 12 AM into 12:00 AM if needed
                # also turns 7 AM into 07:00 AM
                time = (
                    (
                        time.split()[0]
                        if len(time.split()[0].split(":")[0]) == 2
                        else "0" + time.split()[0]
                    )
                    + (":00 " if ":" not in time else " ")
                    + time.split()[1]
                )
                # make sure we're not being jipped
                if not time.split(":")[0].isnumeric() or int(time.split(":")[0]) > 12:
                    await ctx.reply(
                        content="Given time is invalid. Try `12AM`, `12 AM`, `12:00 AM`, or `00:00`.",
                        mention_author=False,
                    )
                    return
            # 24 hour time handler.
            elif (
                ":" in time
                and len(time.split(":")) == 2
                and all(t.isnumeric() and len(t) <= 2 for t in time.split(":"))
                and int(time.split(":")[0]) <= 23
                and int(time.split(":")[1]) <= 59
            ):
                # turn 12:00 into 12:00 PM
                if int(time.split(":")[0]) > 12:
                    fdigit = str(int(time.split(":")[0]) - 12)
                    if len(fdigit) == 1:
                        fdigit = "0" + fdigit
                else:
                    fdigit = (
                        time.split(":")[0] if int(time.split(":")[0]) != 0 else "12"
                    )
                time = (
                    fdigit
                    + ":"
                    + time.split(":")[1]
                    + (" PM" if int(time.split(":")[0]) >= 12 else " AM")
                )
            else:
                await ctx.reply(
                    content="Given time is invalid. Try `12AM`, `12 AM`, `12:00 AM`, or `00:00`.",
                    mention_author=False,
                )
                return

            giventime = (
                datetime.strptime(time, "%I:%M %p")
                .replace(tzinfo=ZoneInfo(tuserdata[tuid]["timezone"]))
                .astimezone(tz=ZoneInfo(suserdata[suid]["timezone"]))
            )
            await ctx.reply(
                content=f"`{time}` for them is `{giventime.strftime('%I:%M %p')}` for you.",
                mention_author=False,
            )
            return
        else:
            userdata, uid = fill_userdata(ctx.author.id if not target else target.id)
            if not userdata[uid]["timezone"]:
                await ctx.reply(
                    content=(
                        "I have no idea what time it is for you. You can set your timezone with `timezone`."
                        if not target
                        else f"I don't know what time it is for {target.display_name}."
                    ),
                    mention_author=False,
                )
                return
            now = datetime.now(ZoneInfo(userdata[uid]["timezone"]))
            await ctx.reply(
                content=f"{'Your' if not target else 'Their'} current time is `{now.strftime('%H:%M, %Y-%m-%d')}`",
                mention_author=False,
            )
            return


async def setup(bot: Bot):
    await bot.add_cog(usertime(bot))
