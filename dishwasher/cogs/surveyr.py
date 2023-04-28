import discord
from discord.ext import commands
from discord.ext.commands import Cog
import json
import config
import datetime
from helpers.checks import check_if_staff
from helpers.configs import get_surveyr_config, config_check
from helpers.surveyr import surveyr_event_types, new_survey, edit_survey, get_surveys


class Surveyr(Cog):
    """
    An open source Pollr clone.
    """

    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Surveyr isn't set up for this server."

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(invoke_without_command=True, aliases=["s"])
    async def survey(self, ctx):
        """[S] Invokes Surveyr."""
        if not config_check(ctx.guild.id, "surveyr"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        surveys = get_surveys(ctx.guild.id)
        if not surveys:
            await ctx.reply(content="There are no surveys yet.", mention_author=False)
        msg = ["**The last few surveys:**"]
        for i, k in enumerate(surveys.reversed()):
            if i == 4:
                break
            event_type = surveyr_event_types[surveys[k]["type"]]
            target = self.bot.fetch_user(surveys[k]["target_id"])
            issuer = self.bot.fetch_user(surveys[k]["issuer_id"])
            msg.append(f"`#{k}` **{event_type.upper()}** of {target} by {issuer}")
        await ctx.reply(content="\n".join(msg), mention_author=False)

    @survey.command(aliases=["r"])
    async def reason(self, ctx, caseid: int, *, reason: str):
        """[S] Edits a case reason."""
        if not config_check(ctx.guild.id, "surveyr"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        survey = get_surveys(ctx.guild.id)[caseid]
        msg = await guild.get_channel(
            get_surveyr_config(member.guild.id, "survey_channel")
        ).fetch_message(survey["post_id"])

        edit_survey(
            ctx.guild.id,
            caseid,
            survey["issuer_id"],
            reason,
            survey["type"],
        )
        content = msg.content.split("\n")
        content[2] = f"**Staff:** {ctx.author} ({ctx.author.id})\n"
        content[3] = f"**Reason:** {reason}"
        await msg.edit(content=content)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if (
            not config_check(member.guild.id, "surveyr")
            or "kicks" not in surveyr_event_types
        ):
            return
        survey_channel = get_surveyr_config(member.guild.id, "survey_channel")

        alog = [
            entry
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.kick
            )
        ]
        msg = await member.guild.get_channel(survey_channel).send(content="⌛")

        cutoff_ts = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=5
        )
        if alog[0].target.id != member.id or alog[0].created_at >= cutoff_ts:
            return

        reason = (
            alog[0].reason
            if alog[0].reason
            else f"No reason was given, {alog[0].user.mention}..."
        )
        caseid, timestamp = new_survey(
            member.guild.id, member.id, msg.id, alog[0].user.id, reason, "kicks"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **KICK** on <t:{timestamp}:f>\n"
                f"**User:** {member} ({member.id})\n"
                f"**Staff:** {alog[0].user} ({alog[0].user.id})\n"
                f"**Reason:** {reason}"
            )
        )

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()
        if not config_check(guild.id, "surveyr") or "bans" not in surveyr_event_types:
            return
        survey_channel = get_surveyr_config(guild.id, "survey_channel")

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )
        ]

        reason = (
            alog[0].reason
            if alog[0].reason
            else f"No reason was given, {alog[0].user.mention}..."
        )
        msg = await guild.get_channel(survey_channel).send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, alog[0].user.id, reason, "bans"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **BAN** on <t:{timestamp}:f>\n"
                f"**User:** {member} ({member.id})\n"
                f"**Staff:** {alog[0].user} ({alog[0].user.id})\n"
                f"**Reason:** {reason}"
            )
        )

        await asyncio.sleep(2)
        try:
            await ctx.guild.get_ban(user)
        except discord.NotFound:
            reason = get_surveys(ctx.guild.id)[cid]["reason"]
            edit_survey(guild.id, caseid, alog[0].user.id, reason, "softbans")
            msg = await guild.get_channel(survey_channel).fetch_message(msg.id)
            content = msg.content.split("\n")
            content[0] = f"`#{caseid}` **SOFTBAN** on <t:{timestamp}:f>\n"
            await msg.edit(content=content)


async def setup(bot):
    await bot.add_cog(Surveyr(bot))
