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
from helpers.configs import (
    get_toss_config,
    get_staff_config,
    get_log_config,
    config_check,
)


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

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["roleban"])
    async def toss(self, ctx, *, user_ids):
        if not config_check(ctx.guild.id, "toss"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)

        toss_pings = ""
        toss_sends = ""
        staff_channel = get_staff_config(ctx.guild.id, "staff_channel")
        modlog_channel = get_log_config(ctx.guild.id, "mlog_thread")

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
            toss_role = ctx.guild.get_role(get_toss_config(ctx.guild.id, "toss_role"))
            toss_channel = ctx.guild.get_channel(
                get_toss_config(ctx.guild.id, "toss_channel")
            )
            for rx in us.roles:
                if rx.name != "@everyone" and rx != toss_role:
                    roles.append(rx)
                    role_ids.append(rx.id)

            try:
                with open(rf"data/toss/{ctx.guild.id}-{us.id}.json", "x") as file:
                    file.write(json.dumps(role_ids))
            except FileExistsError:
                if toss_role in us.roles:
                    await ctx.reply(
                        f"{us.name} is already tossed.", mention_author=False
                    )
                    continue
                else:
                    with open(rf"data/toss/{ctx.guild.id}-{us.id}.json", "w") as file:
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
                toss_sends = (
                    f"{toss_sends}\n**{us.name}**#{us.discriminator} has been tossed."
                )
                bad_roles_msg = ""
                if len(bad_no_good_terrible_roles) > 0:
                    bad_roles_msg = f"\nI was unable to remove the following role(s): **{', '.join(bad_no_good_terrible_roles)}**"

                if staff_channel:
                    await ctx.guild.get_channel(staff_channel).send(
                        f"**{us.name}**#{us.discriminator} has been tossed in {ctx.channel.mention} by {ctx.message.author.name}. {us.mention}\n"
                        f"**ID:** {us.id}\n"
                        f"**Created:** <t:{int(us.created_at.timestamp())}:R> on <t:{int(us.created_at.timestamp())}:f>\n"
                        f"**Joined:** <t:{int(us.joined_at.timestamp())}:R> on <t:{int(us.joined_at.timestamp())}:f>\n"
                        f"**Previous Roles:**{prev_roles}{bad_roles_msg}\n\n"
                        f"{toss_channel.mention}"
                    )

                userlog(
                    ctx.guild.id,
                    us.id,
                    ctx.author,
                    f"[Jump]({ctx.message.jump_url}) to toss event.",
                    "tosses",
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
            f"**Do NOT leave the server, or you will be instantly banned.**\n\n"
            f"⏰ Please respond within `5 minutes`."
        )

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
    async def untoss(self, ctx, *, user_ids):
        if not config_check(ctx.guild.id, "toss"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)
        staff_channel = get_staff_config(ctx.guild.id, "staff_channel")

        for us in user_id_list:
            if us.id == self.bot.application_id:
                await ctx.reply(random_bot_msg(ctx.author.name), mention_author=False)
                continue

            if us.id == ctx.author.id:
                await ctx.reply(random_self_msg(ctx.author.name), mention_author=False)
                continue

            try:
                with open(rf"data/toss/{ctx.guild.id}-{us.id}.json") as file:
                    raw_d = file.read()
                    roles = json.loads(raw_d)
                    print(roles)
                os.remove(rf"data/toss/{ctx.guild.id}-{us.id}.json")
            except FileNotFoundError:
                await ctx.reply(
                    f"{us.name} is not currently tossed.", mention_author=False
                )

            toss_role = ctx.guild.get_role(get_toss_config(ctx.guild.id, "toss_role"))
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
                await ctx.guild.get_channel(
                    get_staff_config(ctx.guild.id, "staff_channel")
                ).send(
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


async def setup(bot):
    await bot.add_cog(ModToss(bot))
