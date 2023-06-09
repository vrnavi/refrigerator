import discord
from discord.ext import commands
from discord.ext.commands import Cog
import json
import config
import datetime
import asyncio
import os
from helpers.checks import check_if_staff
from helpers.sv_config import get_config
from helpers.surveyr import surveyr_event_types, new_survey, edit_survey, get_surveys


class Surveyr(Cog):
    """
    An open source Pollr clone.
    """

    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Surveyr isn't set up for this server."
        self.bancooldown = {}

    def case_handler(self, cases, surveys):
        if cases.isdigit():
            return [int(cases)]
        elif cases == "l":
            return [int(list(surveys)[-1])]
        else:
            try:
                if len(cases.split("-")) != 2:
                    return None
                elif cases.split("-")[1] == "l":
                    return range(int(cases.split("-")[0]), int(list(surveys)[-1]) + 1)
                return range(int(cases.split("-")[0]), int(cases.split("-")[1]) + 1)
            except:
                return None

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(invoke_without_command=True, aliases=["s"])
    async def survey(self, ctx):
        """[S] Invokes Surveyr."""
        if not get_config(ctx.guild.id, "surveyr", "enable"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        surveys = get_surveys(ctx.guild.id)
        if not surveys:
            await ctx.reply(content="There are no surveys yet.", mention_author=False)
        msg = []
        for i, k in enumerate(reversed(surveys)):
            if i == 4:
                break
            event_type = surveyr_event_types[surveys[k]["type"]]
            target = await self.bot.fetch_user(surveys[k]["target_id"])
            issuer = await self.bot.fetch_user(surveys[k]["issuer_id"])
            msg.append(f"`#{k}` **{event_type.upper()}** of {target} by {issuer}")
        await ctx.reply(
            content="**The last few surveys:**\n" + "\n".join(reversed(msg)),
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["r"])
    async def reason(self, ctx, caseids: str, *, reason: str):
        """[S] Edits case reasons."""
        if not get_config(ctx.guild.id, "surveyr", "enable"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_surveys(ctx.guild.id))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to update `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return
        msg = []
        for case in cases:
            try:
                survey = get_surveys(ctx.guild.id)[str(case)]
                msg = await ctx.guild.get_channel(
                    get_config(ctx.guild.id, "surveyr", "survey_channel")
                ).fetch_message(survey["post_id"])

                edit_survey(
                    ctx.guild.id,
                    case,
                    survey["issuer_id"],
                    reason,
                    survey["type"],
                )
                content = msg.content.split("\n")
                content[2] = f"**Staff:** {ctx.author} ({ctx.author.id})"
                content[3] = f"**Reason:** {reason}"
                await msg.edit(content="\n".join(content))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        edited = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Edited `{edited}`.", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["c"])
    async def censor(self, ctx, caseids: str):
        """[S] Censors cases."""
        if not get_config(ctx.guild.id, "surveyr", "enable"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_surveys(ctx.guild.id))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to censor `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return

        for case in cases:
            try:
                survey = get_surveys(ctx.guild.id)[str(case)]
                member = await self.bot.fetch_user(survey["target_id"])
                censored_member = (
                    "`" + " " * len(member.name) + "`#" + member.discriminator
                )
                msg = await ctx.guild.get_channel(
                    get_config(ctx.guild.id, "surveyr", "survey_channel")
                ).fetch_message(survey["post_id"])
                content = msg.content.split("\n")
                content[1] = f"**User:** {censored_member} ({member.id})"
                await msg.edit(content="\n".join(content))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        censored = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Censored `{censored}`.", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["u"])
    async def uncensor(self, ctx, caseids: str):
        """[S] Uncensors cases."""
        if not get_config(ctx.guild.id, "surveyr", "enable"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_surveys(ctx.guild.id))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to uncensor `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return

        for case in cases:
            try:
                survey = get_surveys(ctx.guild.id)[str(case)]
                member = await self.bot.fetch_user(survey["target_id"])
                msg = await ctx.guild.get_channel(
                    get_config(ctx.guild.id, "surveyr", "survey_channel")
                ).fetch_message(survey["post_id"])
                content = msg.content.split("\n")
                content[1] = f"**User:** {member} ({member.id})"
                await msg.edit(content="\n".join(content))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        uncensored = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Uncensored `{uncensored}`.", mention_author=False)

    @commands.guild_only()
    @commands.command(aliases=["d"])
    async def dump(self, ctx, caseids: str):
        """[S] Dumps userids from cases."""
        if not get_config(ctx.guild.id, "surveyr", "enable"):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_surveys(ctx.guild.id))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)

        userids = []
        for case in cases:
            try:
                survey = get_surveys(ctx.guild.id)[str(case)]
                if survey["type"] == "bans":
                    userids.append(str(survey["target_id"]))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        userids = list(dict.fromkeys(userids))
        with open("iddump.txt", "w") as f:
            f.write("\n".join(userids))
        await ctx.reply(file=discord.File("iddump.txt"), mention_author=False)
        os.remove("iddump.txt")

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if (
            not get_config(member.guild.id, "surveyr", "enable")
            or "kicks" not in surveyr_event_types
        ):
            return
        guild = member.guild
        survey_channel = get_config(member.guild.id, "surveyr", "survey_channel")

        # Waiting for Discord's mistimed audit log entry.
        entry = None
        for x in range(60):
            if x == 59:
                return
            async for log in guild.audit_logs(
                before=datetime.datetime.now() + datetime.timedelta(0, 10),
                action=discord.AuditLogAction.kick,
            ):
                if log.target.id == member.id:
                    entry = log
                    break
            if entry:
                break
            else:
                await asyncio.sleep(1)

        if entry.user.id == self.bot.user.id:
            # Recognize audit log reason formats by Dishwasher
            user = guild.get_member_named(entry.reason.split()[2].split("#")[0])
            reason = (
                entry.reason.split("]")[1][1:]
                if entry.reason.split("]")[1][1:]
                else f"No reason was given, {user.mention}..."
            )
        else:
            user = entry.user
            reason = (
                entry.reason
                if entry.reason
                else f"No reason was given, {user.mention}..."
            )

        msg = await guild.get_channel(survey_channel).send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, user.id, reason, "kicks"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **KICK** on <t:{timestamp}:f>\n"
                f"**User:** {member} ({member.id})\n"
                f"**Staff:** {user} ({user.id})\n"
                f"**Reason:** {reason}"
            )
        )
        return

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()
        if (
            not get_config(guild.id, "surveyr", "enable")
            or "bans" not in surveyr_event_types
        ):
            return
        survey_channel = get_config(guild.id, "surveyr", "survey_channel")

        # Waiting for Discord's mistimed audit log entry.
        entry = None
        for x in range(60):
            if x == 59:
                return
            async for log in guild.audit_logs(
                before=datetime.datetime.now() + datetime.timedelta(0, 10),
                action=discord.AuditLogAction.ban,
            ):
                if log.target.id == member.id:
                    entry = log
                    break
            if entry:
                break
            else:
                await asyncio.sleep(1)

        if entry.user.id == self.bot.user.id:
            # Recognize audit log reason formats by Dishwasher
            user = guild.get_member_named(entry.reason.split()[2].split("#")[0])
            reason = (
                entry.reason.split("]")[1][1:]
                if entry.reason.split("]")[1][1:]
                else f"No reason was given, {user.mention}..."
            )
        else:
            user = entry.user
            reason = (
                entry.reason
                if entry.reason
                else f"No reason was given, {user.mention}..."
            )

        msg = await guild.get_channel(survey_channel).send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, user.id, reason, "bans"
        )
        self.bancooldown[guild.id] = member.id

        await msg.edit(
            content=(
                f"`#{caseid}` **BAN** on <t:{timestamp}:f>\n"
                f"**User:** {member} ({member.id})\n"
                f"**Staff:** {user} ({user.id})\n"
                f"**Reason:** {reason}"
            )
        )

        await asyncio.sleep(2)
        try:
            await guild.fetch_ban(member)
        except discord.NotFound:
            reason = get_surveys(guild.id)[str(caseid)]["reason"]
            edit_survey(guild.id, caseid, entry.user.id, reason, "softbans")
            msg = await guild.get_channel(survey_channel).fetch_message(msg.id)
            content = msg.content.split("\n")
            content[0] = f"`#{caseid}` **SOFTBAN** on <t:{timestamp}:f>"
            await msg.edit(content="\n".join(content))
            del self.bancooldown[guild.id]
        return

    @Cog.listener()
    async def on_member_unban(self, guild, member):
        await self.bot.wait_until_ready()
        if (
            not get_config(guild.id, "surveyr", "enable")
            or "unbans" not in surveyr_event_types
        ):
            return
        survey_channel = get_config(guild.id, "surveyr", "survey_channel")

        # Waiting for Discord's mistimed audit log entry.
        entry = None
        for x in range(60):
            if x == 59:
                return
            async for log in guild.audit_logs(
                before=datetime.datetime.now() + datetime.timedelta(0, 10),
                action=discord.AuditLogAction.unban,
            ):
                if log.target.id == member.id:
                    entry = log
                    break
            if entry:
                break
            else:
                await asyncio.sleep(1)

        if entry.user.id == self.bot.user.id:
            # Recognize audit log reason formats by Dishwasher
            user = guild.get_member_named(entry.reason.split()[2].split("#")[0])
            reason = (
                entry.reason.split("]")[1][1:]
                if entry.reason.split("]")[1][1:]
                else f"No reason was given, {user.mention}..."
            )
        else:
            user = entry.user
            reason = (
                entry.reason
                if entry.reason
                else f"No reason was given, {user.mention}..."
            )

        msg = await guild.get_channel(survey_channel).send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, user.id, reason, "unbans"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **UNBAN** on <t:{timestamp}:f>\n"
                f"**User:** {member} ({member.id})\n"
                f"**Staff:** {user} ({user.id})\n"
                f"**Reason:** {reason}"
            )
        )
        return


async def setup(bot):
    await bot.add_cog(Surveyr(bot))
