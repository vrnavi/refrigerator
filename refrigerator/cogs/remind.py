import asyncio
import zoneinfo
import time
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from typing import Dict, Any
import revolt
from revolt.ext import commands
from helpers.messageutils import get_dm_channel
from helpers.embeds import SendableFieldedEmbedBuilder
from helpers.dishtimer import add_job, get_crontab, delete_job


class Remind(commands.Cog):
    def __init__(self, bot: commands.CommandsClient):
        self.qualified_name = "remind"
        self.bot = bot
        self.scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={
                "coalesce": False,
                "misfire_grace_time": None,
                "replace_existing": True,
            },
        )
        self.scheduler.timezone = zoneinfo.ZoneInfo("UTC")

    def cog_load(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._start())

    def cog_unload(self):
        self.bot.log.info("Shutting down reminders schedule")
        self.scheduler.shutdown(False)

    async def _start(self):
        if not hasattr(self.bot, "state"):
            await self.bot.wait_for("ready")
        self.bot.log.info("Starting reminders scheduler")
        ctab = get_crontab()
        if ctab:
            for ts in ctab["remind"]:
                for uid in ctab["remind"][ts]:
                    self.scheduler.add_job(
                        func=self._send_reminder,
                        trigger="date",
                        kwargs={
                            "user_id": uid,
                            "timestamp": int(ts),
                            "details": ctab["remind"][ts][uid],
                        },
                        id=f"remind:{uid}:{ts}",
                        next_run_time=datetime.utcfromtimestamp(int(ts)),
                    )
        self.scheduler.start()

    async def _send_reminder(
        self, user_id: str, timestamp: int, details: Dict[str, Any]
    ):
        user = self.bot.get_user(user_id)
        text = details["text"]
        added_on = details["added"]
        target = self.bot.get_user(user_id)
        original_timestamp = int(
            datetime.strptime(added_on, "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        embed = SendableFieldedEmbedBuilder(
            title="⏰ Reminder",
            description=f"You asked to be reminded <t:{original_timestamp}:R> on <t:{original_timestamp}:f>.",
            fields=[("📝 Contents", f"{text}")],
            color="#9cd8df",
        ).build()

        channel = await get_dm_channel(self.bot, target)
        await channel.send(embed=embed)
        delete_job(timestamp, "remind", user_id)

    @commands.group()
    async def reminders(self, ctx: commands.Context):
        """[U] Lists your reminders."""
        ctab = get_crontab()
        uid = ctx.author.id
        embed = revolt.SendableEmbed(
            title="Your current reminders...",
            description="",
            colour="#9cd8df"
        )
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
            embed.description += f"#### `{idx}` | Reminder on <t:{jobtimestamp}:F>, Added <t:{addedtime}:R>\n{job_details['text']}\n"

        await ctx.message.reply(embed=embed, mention=False)

    @reminders.command()
    async def remove(self, ctx: commands.Context, number: str = None):
        """[U] Removes one of your reminders."""
        if not number:
            await ctx.message.reply(
                "Please enter the number of reminder.", mention=False
            )
            return
        try:
            number = int(number)
        except ValueError:
            await ctx.message.reply("This reminder does not exist.", mention=False)
            return
        ctab = get_crontab()
        uid = ctx.author.id
        idx = 0
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            idx = idx + 1
            if idx == number:
                delete_job(jobtimestamp, "remind", uid)
                self.scheduler.remove_job(f"remind:{uid}:{jobtimestamp}")
                await ctx.message.reply("Reminder removed.", mention=False)
                return
        await ctx.message.reply("This reminder does not exist.", mention=False)

    @commands.command(aliases=["remindme"])
    async def remind(self, ctx: commands.Context, when: str, *, text: str = None):
        """[U] Reminds you about something."""
        if not text:
            # revolt.py don't even know what is default values :(
            text = "something"
        current_timestamp = time.time()
        if when.isdigit() and len(when) == 10:
            # Timestamp provided, just use that.
            expiry_timestamp = int(when)
        else:
            expiry_timestamp = self.bot.parse_time(when)

        if current_timestamp + 59 > expiry_timestamp:
            await ctx.message.reply(
                "Either timespan too short (minimum 1 minute from now) or incorrect format (number then unit of time, or timestamp).\n"
                "Example: `remindme 3h Check the dishwasher.`",
                mention=False,
            )
            return

        expiry_datetime = datetime.utcfromtimestamp(expiry_timestamp)
        added_on = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        add_job(
            "remind",
            ctx.author.id,
            {"text": text, "added": added_on},
            expiry_timestamp,
        )
        self.scheduler.add_job(
            func=self._send_reminder,
            trigger="date",
            kwargs={
                "user_id": ctx.author.id,
                "timestamp": expiry_timestamp,
                "details": {"text": text, "added": added_on},
            },
            id=f"remind:{ctx.author.id}:{expiry_timestamp}",
            next_run_time=datetime.utcfromtimestamp(expiry_timestamp),
            replace_existing=True,
        )

        embed = SendableFieldedEmbedBuilder(
            title="⏰ Reminder added.",
            description=f"You will be reminded in DMs <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f>.",
            color="#9cd8df",
            fields=[("📝 Contents", f"{text}")],
        ).build()

        await ctx.message.reply(embed=embed)


def setup(bot: commands.CommandsClient):
    return Remind(bot)
