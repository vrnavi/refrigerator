# This Cog contains code from Tosser2, which was made by OblivionCreator.
import discord
import json
import os
import asyncio
import random
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.userlogs import userlog
from helpers.placeholders import random_self_msg, random_bot_msg
from helpers.store import LAST_UNROLEBAN
from helpers.sv_config import get_config


class ModToss(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Tossing isn't enabled for this server."

    def get_user_list(self, ctx, user_ids):
        user_id_list = []
        invalid_ids = []

        if user_ids.isnumeric():
            tmp_user = ctx.guild.get_member(int(user_ids))
            if tmp_user is not None:
                user_id_list.append(tmp_user)
            else:
                invalid_ids.append(user_ids)
        else:
            if ctx.message.mentions:
                for u in ctx.message.mentions:
                    user_id_list.append(u)
            user_ids_split = user_ids.split()
            for n in user_ids_split:
                if n.isnumeric():
                    user = ctx.guild.get_member(int(n))
                    if user is not None:
                        user_id_list.append(user)
                    else:
                        invalid_ids.append(n)

        return user_id_list, invalid_ids

    def is_rolebanned(self, member, hard=True):
        roleban = [
            r
            for r in member.guild.roles
            if r.id == get_config(member.guild.id, "toss", "toss_role")
        ]
        if roleban:
            if get_config(member.guild.id, "toss", "toss_role") in [
                r.id for r in member.roles
            ]:
                if hard:
                    return len([r for r in member.roles if not (r.managed)]) == 2
                return True

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def sessions(self, ctx):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        embed = discord.Embed(
            title="👁‍🗨 Toss Channel Sessions...",
            color=ctx.author.color,
            timestamp=datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        for c in get_config(ctx.guild.id, "toss", "toss_channels"):
            if c in [g.name for g in ctx.guild.channels]:
                if not os.listdir(f"{self.bot.server_data}/{ctx.guild.id}/toss/{c}"):
                    embed.add_field(
                        name=f"🟡 #{c}",
                        value="__Error__\nChannel exists yet no users...\nIf you see this, please delete the channel.",
                        inline=False,
                    )
                else:
                    userlist = "\n".join(
                        [
                            f"> {user.global_name} [{user}]"
                            for user in [
                                await self.bot.fetch_user(u)
                                for u in [uf[:-4] for uf in os.listdirs()]
                            ]
                        ]
                    )
                    embed.add_field(
                        name=f"🔴 #{c}",
                        value=f"__Occupied__\n{userlist}",
                        inline=False,
                    )
            else:
                embed.add_field(name=f"🟢 #{c}", value="__Available__", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["roleban"])
    async def toss(self, ctx, *, user_ids):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)

        toss_pings = ""
        toss_sends = ""
        online = False
        staff_channel = get_config(ctx.guild.id, "staff", "staff_channel")
        modlog_channel = get_config(ctx.guild.id, "logs", "mlog_thread")

        # todo: find an available session and use that
        if all(
            [
                g in ctx.guild.channels
                for g in get_config(ctx.guild.id, "toss", "toss_channels")
            ]
        ):
            return await ctx.reply(
                content="I cannot toss them. All sessions are currently in use.",
                mention_author=False,
            )
        for c in get_config(ctx.guild.id, "toss", "toss_channels"):
            if c not in [g.name for g in ctx.guild.channels]:
                pass  # make the channel and save this

        for us in user_id_list:
            if us.id == ctx.author.id:
                await ctx.reply(
                    random_self_msg(ctx.author.name),
                    mention_author=False,
                )
                continue

            if us.id == self.bot.application_id:
                await ctx.reply(
                    random_bot_msg(ctx.author.name),
                    mention_author=False,
                )
                continue

            roles = []
            role_ids = []
            toss_role = ctx.guild.get_role(
                get_config(ctx.guild.id, "toss", "toss_role")
            )
            toss_channel = ctx.guild.get_channel(
                get_config(ctx.guild.id, "toss", "toss_channel")
            )
            for rx in us.roles:
                if rx.name != "@everyone" and rx != toss_role:
                    roles.append(rx)
                    role_ids.append(rx.id)

            if not os.path.exists(f"{self.bot.server_data}/{ctx.guild.id}/toss"):
                os.makedirs(f"{self.bot.server_data}/{ctx.guild.id}/toss")

            try:
                with open(
                    rf"{self.bot.server_data}/{ctx.guild.id}/toss/{us.id}.json", "x"
                ) as file:
                    file.write(json.dumps(role_ids))
            except FileExistsError:
                if toss_role in us.roles:
                    await ctx.reply(
                        f"{us.name} is already tossed.", mention_author=False
                    )
                    continue
                else:
                    with open(
                        rf"{self.bot.server_data}/{ctx.guild.id}/toss/{us.id}.json", "w"
                    ) as file:
                        file.write(json.dumps(role_ids))

            prev_roles = ""

            for r in roles:
                prev_roles = f"{prev_roles} `{r.name}`"

            try:
                await us.add_roles(toss_role, reason="User tossed.")
                bad_no_good_terrible_roles = []
                roles_actual = []
                if len(roles) > 0:
                    for rr in roles:
                        if not rr.is_assignable():
                            bad_no_good_terrible_roles.append(rr.name)
                        else:
                            roles_actual.append(rr)
                    await us.remove_roles(
                        *roles_actual,
                        reason=f"User tossed by {ctx.author} ({ctx.author.id})",
                        atomic=False,
                    )

                toss_pings = f"{toss_pings} {us.mention}"
                toss_sends = f"{toss_sends}\n**{us}** has been tossed."
                bad_roles_msg = ""
                if len(bad_no_good_terrible_roles) > 0:
                    bad_roles_msg = f"\nI was unable to remove the following role(s): **{', '.join(bad_no_good_terrible_roles)}**"

                userlog(
                    ctx.guild.id,
                    us.id,
                    ctx.author,
                    f"[Jump]({ctx.message.jump_url}) to toss event.",
                    "tosses",
                )

                if us.raw_status != "offline":
                    online = True

                if staff_channel:
                    await ctx.guild.get_channel(staff_channel).send(
                        f"**{us}** has been tossed in {ctx.channel.mention} by {ctx.message.author.name}. {us.mention}\n"
                        f"**ID:** {us.id}\n"
                        f"**Created:** <t:{int(us.created_at.timestamp())}:R> on <t:{int(us.created_at.timestamp())}:f>\n"
                        f"**Joined:** <t:{int(us.joined_at.timestamp())}:R> on <t:{int(us.joined_at.timestamp())}:f>\n"
                        f"**Previous Roles:**{prev_roles}{bad_roles_msg}\n\n"
                        f"{toss_channel.mention}"
                    )

                if modlog_channel:
                    embed = discord.Embed(
                        color=discord.Colour.from_str("#FF0000"),
                        title="🚷 Toss",
                        description=f"{us.mention} was tossed by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]",
                        timestamp=datetime.now(),
                    )
                    embed.set_footer(
                        text=self.bot.user.name, icon_url=self.bot.user.display_avatar
                    )
                    embed.set_author(
                        name=f"{self.bot.escape_message(us)}",
                        icon_url=f"{us.display_avatar.url}",
                    )
                    embed.add_field(
                        name=f"👤 User",
                        value=f"**{self.bot.escape_message(us)}**\n{us.mention} ({us.id})",
                        inline=True,
                    )
                    embed.add_field(
                        name=f"🛠️ Staff",
                        value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
                        inline=True,
                    )
                    mlog = await self.bot.fetch_channel(modlog_channel)
                    await mlog.send(embed=embed)

            except commands.MissingPermissions:
                invalid_ids.append(us.name)

        invalid_string = ""
        if len(invalid_ids) > 0:
            for iv in invalid_ids:
                invalid_string = f"{invalid_string}, {iv}"
            invalid_string = f"\nI was unable to toss these users: {invalid_string[2:]}"

        if len(invalid_string) > 0:
            await ctx.reply(invalid_string, mention_author=False)

        hardmsg = ""
        if (
            ctx.channel.permissions_for(ctx.guild.default_role).read_messages
            or len(ctx.channel.members) >= 100
        ):
            hardmsg = "Please change the topic. **Discussion of tossed users will lead to warnings.**"
        await ctx.reply(f"{toss_sends}\n\n{hardmsg}", mention_author=False)

        await toss_channel.send(
            f"{toss_pings}\nYou were tossed by {ctx.message.author.name}.\n"
            f'*For your reference, a "toss" is where a Staff member wishes to speak with you, one on one.*\n'
            f"**Do NOT leave the server, or you will be instantly banned.**"
        )

        if online:
            await toss_channel.send(f"⏰ Please respond within `5 minutes`.")

            def check(m):
                return m.author in user_id_list and m.channel == toss_channel

            try:
                msg = await self.bot.wait_for("message", timeout=60 * 5, check=check)
            except asyncio.TimeoutError:
                pokemsg = await toss_channel.send(f"{ctx.author.mention}")
                await pokemsg.edit(content="⏰", delete_after=5)
            else:
                pokemsg = await toss_channel.send(f"{ctx.author.mention}")
                await pokemsg.edit(
                    content="⏰🔨 Tossed user sent a message. Timer destroyed.",
                    delete_after=5,
                )

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["unroleban"])
    async def untoss(self, ctx, *, user_ids=None):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)

        if not user_ids:
            if LAST_UNROLEBAN.isset(ctx.guild.id) and LAST_UNROLEBAN.diff(
                ctx.guild.id, ctx.message.created_at
            ) < get_config(ctx.guild.id, "archive", "unroleban_expiry"):
                user_ids = str(LAST_UNROLEBAN.guild_set[ctx.guild.id]["user_id"])
                if not get_config(ctx.guild.id, "archive", "enable"):
                    LAST_UNROLEBAN.unset(ctx.guild.id)
            else:
                return await ctx.reply(
                    content="There's nobody in the roleban cache.\nYou'll need to untoss with a ping or ID.",
                    mention_author=False,
                )

        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)
        staff_channel = get_config(ctx.guild.id, "staff", "staff_channel")

        for us in user_id_list:
            if us.id == self.bot.application_id:
                await ctx.reply(random_bot_msg(ctx.author.name), mention_author=False)
                continue

            if us.id == ctx.author.id:
                await ctx.reply(random_self_msg(ctx.author.name), mention_author=False)
                continue

            try:
                with open(
                    rf"{self.bot.server_data}/{ctx.guild.id}/toss/{us.id}.json"
                ) as file:
                    raw_d = file.read()
                    roles = json.loads(raw_d)
                    print(roles)
                os.remove(rf"{self.bot.server_data}/{ctx.guild.id}/toss/{us.id}.json")
            except FileNotFoundError:
                await ctx.reply(
                    f"{us.name} is not currently tossed.", mention_author=False
                )

            toss_role = ctx.guild.get_role(
                get_config(ctx.guild.id, "toss", "toss_role")
            )
            roles_actual = []
            restored = ""
            for r in roles:
                temp_role = ctx.guild.get_role(r)
                if temp_role is not None and temp_role.is_assignable():
                    roles_actual.append(temp_role)
            await us.add_roles(
                *roles_actual,
                reason=f"Untossed by {ctx.author} ({ctx.author.id})",
                atomic=False,
            )

            for rx in roles_actual:
                restored = f"{restored} `{rx.name}`"

            await us.remove_roles(
                toss_role,
                reason=f"Untossed by {ctx.author} ({ctx.author.id})",
            )
            await ctx.reply(
                f"**{us.name}**#{us.discriminator} has been untossed.\n**Roles Restored:**{restored}",
                mention_author=False,
            )
            if staff_channel:
                await ctx.guild.get_channel(staff_channel).send(
                    f"**{us.name}**#{us.discriminator} has been untossed in {ctx.channel.mention} by {ctx.author.name}.\n**Roles Restored:** {restored}"
                )

        invalid_string = ""

        if len(invalid_ids) > 0:
            for iv in invalid_ids:
                invalid_string = f"{invalid_string}, {iv}"
            invalid_string = (
                f"\nI was unable to untoss these users: {invalid_string[2:]}"
            )

        if len(invalid_string) > 0:
            await ctx.reply(invalid_string, mention_author=False)

    @Cog.listener()
    async def on_member_remove(self, member):
        if self.is_rolebanned(member):
            staff_channel = get_config(member.guild.id, "staff", "staff_channel")
            if staff_channel:
                try:
                    await member.guild.fetch_ban(member)
                except NotFound:
                    await member.guild.get_channel(staff_channel).send(
                        f"**{member}** left while tossed.\nLaugh at this user!"
                    )
                else:
                    await member.guild.get_channel(staff_channel).send(
                        f"**{member}** finally got banned while tossed."
                    )

            LAST_UNROLEBAN.set(
                member.guild.id,
                member.id,
                datetime.utcnow().replace(tzinfo=timezone.utc),
            )

    @Cog.listener()
    async def on_member_update(self, before, after):
        if self.is_rolebanned(before) and not self.is_rolebanned(after):
            LAST_UNROLEBAN.set(
                after.guild.id,
                after.id,
                datetime.utcnow().replace(tzinfo=timezone.utc),
            )


async def setup(bot):
    await bot.add_cog(ModToss(bot))
