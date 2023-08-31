import config
import time
import traceback
import random
import shutil
import os
from datetime import datetime, timezone
from discord.ext import tasks
import revolt
from revolt.ext import commands
from helpers.dishtimer import get_crontab, delete_job
from helpers.messageutils import get_dm_channel
from helpers.embeds import SendableFieldedEmbedBuilder
from helpers.checks import check_if_staff, check_only_server


class Dishtimer(commands.Cog):
    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot
        self.minutely.start()
        self.hourly.start()
        self.daily.start()

    def cog_unload(self):
        self.minutely.cancel()
        self.hourly.cancel()
        self.daily.cancel()

    async def send_data(self):
        log_channel: revolt.TextChannel = self.bot.get_channel(config.bot_logchannel)
        data_files = [revolt.File(fpath) for fpath in self.bot.data["wanted_jsons"]]
        await log_channel.send("Hourly data backups:", files=data_files)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def listjobs(self, ctx: commands.Context):
        """[S] Lists timed Dishtimer jobs."""
        ctab = get_crontab()
        fields = []
        for jobtype in ctab:
            for jobtimestamp in ctab[jobtype]:
                for job_name in ctab[jobtype][jobtimestamp]:
                    job_details = repr(ctab[jobtype][jobtimestamp][job_name])
                    fields.append((f"{jobtype} for {job_name}", f"Executes on <t:{jobtimestamp}:F>.\nJSON data: {job_details}"))
        await ctx.send(embed=SendableFieldedEmbedBuilder(title=f"Active Dishtimer jobs", fields=fields).build())

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["removejob"])
    async def deletejob(self, ctx: commands.Context, timestamp: str, job_type: str, job_name: str):
        """[S] Removes a timed Dishtimer job.

        You'll need to supply:
        - timestamp (like 1545981602)
        - job type (like "unban")
        - job name (userid, like 420332322307571713)

        You can get all 3 from listjobs command."""
        delete_job(timestamp, job_type, job_name)
        await ctx.send(f"{ctx.author.mention}: Deleted!")

    async def do_jobs(self, ctab, jobtype, timestamp):
        log_channel: revolt.TextChannel = self.bot.get_channel(config.bot_logchannel)
        for job_name in ctab[jobtype][timestamp]:
            try:
                job_details = ctab[jobtype][timestamp][job_name]
                if jobtype == "unban":
                    target_guild = self.bot.get_server(job_details["guild"])
                    target_member = await target_guild.fetch_member(job_name)
                    delete_job(timestamp, jobtype, job_name)
                    await target_member.unban()
                elif jobtype == "remind":
                    text = job_details["text"]
                    added_on = job_details["added"]
                    target = await self.bot.fetch_user(job_name)
                    original_timestamp = (
                        datetime.strptime(added_on, "%Y-%m-%d %H:%M:%S")
                        .replace(tzinfo=timezone.utc)
                        .astimezone()
                        .strftime("%s")
                    )
                    if target:
                        channel = await get_dm_channel(self.bot, target)
                        await channel.send(embed=SendableFieldedEmbedBuilder(
                            title="⏰ Reminder",
                            description=f"You asked to be reminded <t:{original_timestamp}:R> on <t:{original_timestamp}:f>.",
                            fields=[("📝 Contents", f"{text}")],
                        ).build())
                    delete_job(timestamp, jobtype, job_name)
            except:
                # Don't kill cronjobs if something goes wrong.
                delete_job(timestamp, jobtype, job_name)
                await log_channel.send(
                    "Crondo has errored, job deleted: ```"
                    f"{traceback.format_exc()}```"
                )

    async def clean_channel(self, channel_id):
        log_channel: revolt.TextChannel = self.bot.get_channel(config.bot_logchannel)
        channel: revolt.TextChannel = self.bot.get_channel(channel_id)
        try:
            done_cleaning = False
            count = 0
            while not done_cleaning:
                messages = await channel.history(limit=100)
                purge_res = await channel.delete_messages(messages)
                count += len(messages)
                if len(purge_res) != 100:
                    done_cleaning = True
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cronclean has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(minutes=1)
    async def minutely(self):
        log_channel: revolt.TextChannel = self.bot.get_channel(config.bot_logchannel)
        try:
            ctab = get_crontab()
            timestamp = time.time()
            for jobtype in ctab:
                for jobtimestamp in ctab[jobtype]:
                    if timestamp > int(jobtimestamp):
                        await self.do_jobs(ctab, jobtype, jobtimestamp)

            # Handle clean channels
            for clean_channel in config.minutely_clean_channels:
                await self.clean_channel(clean_channel)
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-minutely has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(hours=1)
    async def hourly(self):
        log_channel: revolt.TextChannel = self.bot.get_channel(config.bot_logchannel)
        try:
            # Handle clean channels
            for clean_channel in config.hourly_clean_channels:
                await self.clean_channel(clean_channel)
            # Change playing status.
            await self.bot.edit_status(
                text="Listening to " + random.choice(config.game_names), presence=revolt.PresenceType.online
            )
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-hourly has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(hours=24)
    async def daily(self):
        log_channel: revolt.TextChannel = self.bot.get_channel(config.bot_logchannel)
        try:
            shutil.make_archive("data_backup", "zip", self.bot.data["all_data"])
            for m in config.bot_managers:
                channel = await get_dm_channel(self.bot, self.bot.get_user(m))
                await channel.send(
                    content="Daily backups:",
                    attachments=[revolt.File("data_backup.zip")]
                )
            os.remove("data_backup.zip")
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-daily has errored: ```{traceback.format_exc()}```"
            )


def setup(bot):
   return Dishtimer(bot)
