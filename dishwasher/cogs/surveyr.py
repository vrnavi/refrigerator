import discord
from discord.ext.commands import Cog
import json
import config
import datetime
from helpers.checks import check_if_staff
from helpers.configs import get_surveyr_config, config_check
from helpers.surveyr import surveyr_event_types, new_survey, get_surveys


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
    async def survey(self, ctx, caseid: int = None):
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
            guild.id, member.id, msg.id, alog[0].user, reason, "bans"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **BAN** on <t:{timestamp}:f>\n"
                f"**User:** {member} ({member.id})\n"
                f"**Staff:** {alog[0].user} ({alog[0].user.id})\n"
                f"**Reason:** {reason}"
            )
        )


async def setup(bot):
    await bot.add_cog(Surveyr(bot))
