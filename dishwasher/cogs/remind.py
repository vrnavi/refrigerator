import discord
import asyncio
import time
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.dishtimer import add_job, get_crontab


class Remind(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def reminders(self, ctx):
        """[U] Lists your reminders."""
        ctab = get_crontab()
        uid = str(ctx.author.id)
        embed = discord.Embed(title=f"Your current reminders...", color=ctx.author.color, timestamp=datetime.datetime.now())
        embed.set_author(
            icon_url=ctx.author.display_avatar.url, name=ctx.author.display_name
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            job_details = ctab["remind"][jobtimestamp][uid]
            addedtime = datetime.strptime(job_details['added'], "%Y-%m-%d %H:%M:%S").strftime("%s")
            embed.add_field(
                name=f"Reminder on <t:{jobtimestamp}:F>",
                value=f"*Added <t:{addedtime}:R>*\n"
                f"{job_details['text']}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["remindme"])
    async def remind(self, ctx, when: str, *, text: str = "something"):
        """[U] Reminds you about something."""
        #        if ctx.guild:
        #            await ctx.message.delete()
        current_timestamp = time.time()
        expiry_timestamp = self.bot.parse_time(when)

        if current_timestamp + 5 > expiry_timestamp:
            msg = await ctx.message.reply(
                f"Either timespan too short (minimum 5 seconds) or incorrect format (number then unit of time).\nExample: `remindme 3h Check the dishwasher.`",
                mention_author=False,
            )
            return

        expiry_datetime = datetime.utcfromtimestamp(expiry_timestamp)
        duration_text = self.bot.get_relative_timestamp(
            time_to=expiry_datetime, include_to=False, humanized=True
        )

        safe_text = await commands.clean_content().convert(ctx, str(text))
        added_on = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        add_job(
            "remind",
            ctx.author.id,
            {"text": safe_text, "added": added_on},
            expiry_timestamp,
        )

        msg = await ctx.message.reply(
            f"You'll be reminded in "
            f"DMs about `{safe_text}` in {duration_text} (<t:{expiry_timestamp}:f>).",
            mention_author=False,
        )


async def setup(bot):
    await bot.add_cog(Remind(bot))
