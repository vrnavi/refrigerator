import discord
import asyncio
import time
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.dishtimer import add_job, get_crontab, delete_job


class Remind(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def reminders(self, ctx):
        """[U] Lists your reminders."""
        ctab = get_crontab()
        uid = str(ctx.author.id)
        embed = discord.Embed(
            title="Your current reminders...",
            color=ctx.author.color,
            timestamp=datetime.now(),
        )
        embed.set_author(
            icon_url=ctx.author.display_avatar.url, name=ctx.author.display_name
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        idx = 0
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            idx = idx + 1
            job_details = ctab["remind"][jobtimestamp][uid]
            addedtime = int(
                datetime.strptime(
                    f"{job_details['added']} -0000", "%Y-%m-%d %H:%M:%S %z"
                ).timestamp()
            )
            embed.add_field(
                name=f"`{idx}` | Reminder on <t:{jobtimestamp}:F>",
                value=f"*Added <t:{addedtime}:R>.*\n" f"{job_details['text']}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @reminders.command()
    async def remove(self, ctx, number: int):
        """[U] Removes one of your reminders."""
        ctab = get_crontab()
        uid = str(ctx.author.id)
        idx = 0
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            idx = idx + 1
            if idx == number:
                delete_job(jobtimestamp, "remind", uid)
                await ctx.reply(content="Reminder removed.", mention_author=False)
                return
        await ctx.reply(content="This reminder does not exist.", mention_author=False)

    @commands.command(aliases=["remindme"])
    async def remind(self, ctx, when: str, *, text: str = "something"):
        """[U] Reminds you about something."""
        current_timestamp = time.time()
        expiry_timestamp = self.bot.parse_time(when)

        if current_timestamp + 59 > expiry_timestamp:
            msg = await ctx.message.reply(
                "Either timespan too short (minimum 1 minute) or incorrect format (number then unit of time).\nExample: `remindme 3h Check the dishwasher.`",
                mention_author=False,
            )
            return

        expiry_datetime = datetime.utcfromtimestamp(expiry_timestamp)

        safe_text = await commands.clean_content().convert(ctx, str(text))
        added_on = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        add_job(
            "remind",
            ctx.author.id,
            {"text": safe_text, "added": added_on},
            expiry_timestamp,
        )

        embed = discord.Embed(
            title="⏰ Reminder added.",
            description=f"You will be reminded in DMs <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f>.",
            color=ctx.author.color,
            timestamp=datetime.now(),
        )
        embed.set_author(
            icon_url=ctx.author.display_avatar.url, name=ctx.author.display_name
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(
            name="📝 Contents",
            value=f"{safe_text}",
            inline=False,
        )

        msg = await ctx.message.reply(
            embed=embed,
            mention_author=False,
        )


async def setup(bot):
    await bot.add_cog(Remind(bot))
