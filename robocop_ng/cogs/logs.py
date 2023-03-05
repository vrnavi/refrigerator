import discord
from discord.ext.commands import Cog
import json
import re
import config
import datetime
from helpers.restrictions import get_user_restrictions
from helpers.checks import check_if_staff


class Logs(Cog):
    """
    Logs join and leave messages, bans and unbans, and member changes.
    """

    def __init__(self, bot):
        self.bot = bot
        self.invite_re = re.compile(
            r"((discord\.gg|discordapp\.com/" r"+invite)/+[a-zA-Z0-9-]+)", re.IGNORECASE
        )
        self.name_re = re.compile(r"[a-zA-Z0-9].*")
        self.clean_re = re.compile(r"[^a-zA-Z0-9_ ]+", re.UNICODE)
        # All lower case, no spaces, nothing non-alphanumeric
        susp_hellgex = "|".join(
            [r"\W*".join(list(word)) for word in config.suspect_words]
        )
        self.susp_hellgex = re.compile(susp_hellgex, re.IGNORECASE)

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()

        if member.guild.id not in config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(config.log_channel)
        escaped_name = self.bot.escape_message(member)

        # Attempt to correlate the user joining with an invite
        with open("data/invites.json", "r") as f:
            invites = json.load(f)

        real_invites = await member.guild.invites()

        # Add unknown active invites. Can happen if invite was manually created
        for invite in real_invites:
            if invite.id not in invites:
                invites[invite.id] = {
                    "uses": 0,
                    "url": invite.url,
                    "max_uses": invite.max_uses,
                    "code": invite.code,
                }

        probable_invites_used = []
        items_to_delete = []
        # Look for invites whose usage increased since last lookup
        for id, invite in invites.items():
            real_invite = next((x for x in real_invites if x.id == id), None)

            if real_invite is None:
                # Invite does not exist anymore. Was either revoked manually
                # or the final use was used up
                probable_invites_used.append(invite)
                items_to_delete.append(id)
            elif invite["uses"] < real_invite.uses:
                probable_invites_used.append(invite)
                invite["uses"] = real_invite.uses

        # Delete used up invites
        for id in items_to_delete:
            del invites[id]

        # Save invites data.
        with open("data/invites.json", "w") as f:
            f.write(json.dumps(invites))

        # Prepare the invite correlation message
        if len(probable_invites_used) == 1:
            invite_used = probable_invites_used[0]["code"]
        elif len(probable_invites_used) == 0:
            invite_used = "Unknown"
        else:
            invite_used = "One of: "
            invite_used += ", ".join([x["code"] for x in probable_invites_used])

        # UNUSED: Check if user account is older than 15 minutes
        # age = member.joined_at - member.created_at
        # if age < config.min_age:
        #    try:
        #        await member.send(
        #            f"Your account is too new to "
        #            f"join this server."
        #            " Please try again later."
        #        )
        #        sent = True
        #    except discord.errors.Forbidden:
        #        sent = False
        #    await member.kick(reason="Too new")
        #
        #    msg = (
        #        f"🚨 **Account too new**: {member.mention} | "
        #        f"{escaped_name}\n"
        #        f"🗓 __Creation__: {member.created_at}\n"
        #        f"🕓 Account age: {age}\n"
        #        f"✉ Joined with: {invite_used}\n"
        #        f"🏷 __User ID__: {member.id}"
        #    )
        #    if not sent:
        #        msg += (
        #            "\nThe user has disabled direct messages, "
        #            "so the reason was not sent."
        #        )
        #    await log_channel.send(msg)
        #    return
            
        # Prepare embed msg
        embeds = []
        embed = discord.Embed(
            color=discord.Color.lighter_gray(), title="📥 User Joined", description=f"<@{member.id}> ({member.id})", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{escaped_name}", icon_url=f"{member.display_avatar.url}")
        embed.set_thumbnail(url=f"{member.display_avatar.url}")
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
            inline=True
        )
        embed.add_field(
            name="📨 Invite used:",
            value=f"{invite_used}",
            inline=True
        )
        embeds.append(embed)

        # Handles user restrictions
        # Basically, gives back muted role to users that leave with it.
        rsts = get_user_restrictions(member.id)
        roles = [discord.utils.get(member.guild.roles, id=rst) for rst in rsts]
        await member.add_roles(*roles)

        # Real hell zone.
        with open("data/userlog.json", "r") as f:
            warns = json.load(f)
        try:
            if len(warns[str(member.id)]["warns"]) == 0:
                await log_channel.send(embeds=embeds)
            else:
                embed = discord.Embed(
                    color=discord.Color.red(), title="⚠️ This user has warnings!", timestamp=datetime.datetime.now()
                )
                embed.set_footer(text="Dishwasher")
                for idx, warn in enumerate(warns[str(member.id)]["warns"]):
                    timestamp = datetime.datetime.strptime(warn['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%s")
                    embed.add_field(
                        name=f"Warn {idx + 1}: <t:{timestamp}:f> (<t:{timestamp}:R>)",
                        value=f"__Issuer:__ <@{warn['issuer_id']}> ({warn['issuer_id']})\n"
                        f"\n__Reason:__ {warn['reason']}",
                        inline=False,
                    )
                embeds.append(embed)
                await log_channel.send(embeds=embeds)
        except KeyError:  # if the user is not in the file
            await log_channel.send(embeds=embeds)

    async def do_spy(self, message):
        if message.author.bot:
            return

        if check_if_staff(message):
            return

        alert = False
        cleancont = self.clean_re.sub("", message.content).lower()
        msg = (
            f"🚨 Suspicious message by {message.author.mention} "
            f"({message.author.id}):"
        )

        invites = self.invite_re.findall(message.content)
        for invite in invites:
            msg += f"\n- Has invite: https://{invite[0]}"
            alert = True

        for susp_word in config.suspect_words:
            if susp_word in cleancont and not any(
                ok_word in cleancont for ok_word in config.suspect_ignored_words
            ):
                msg += f"\n- Contains suspicious word: `{susp_word}`"
                alert = True

        if alert:
            msg += f"\n\nJump: <{message.jump_url}>"
            spy_channel = self.bot.get_channel(config.spylog_channel)

            # Bad Code :tm:, blame retr0id
            message_clean = message.content.replace("*", "").replace("_", "")
            regd = self.susp_hellgex.sub(
                lambda w: "**{}**".format(w.group(0)), message_clean
            )

            # Show a message embed
            embed = discord.Embed(description=regd)
            embed.set_author(
                name=message.author.display_name, icon_url=message.author.display_avatar.url
            )

            await spy_channel.send(msg, embed=embed)

    async def do_nickcheck(self, message):
        compliant = self.name_re.fullmatch(message.author.display_name)
        if compliant:
            return

        msg = (
            f"R11 violating name by {message.author.mention} " f"({message.author.id})."
        )

        spy_channel = self.bot.get_channel(config.spylog_channel)
        await spy_channel.send(msg)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if message.channel.id not in config.spy_channels:
            return

        await self.do_spy(message)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.wait_until_ready()
        if after.channel.id not in config.spy_channels or after.author.bot:
            return

        # If content is the same, just skip over it
        # This usually means that something embedded.
        if before.clean_content == after.clean_content:
            return

        await self.do_spy(after)

        # U+200D is a Zero Width Joiner stopping backticks from breaking the formatting
        before_content = before.clean_content.replace("`", "`\u200d")
        after_content = after.clean_content.replace("`", "`\u200d")

        log_channel = self.bot.get_channel(config.log_channel)

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.light_gray(), title="📝 Message Edit", description=f"<@{after.author.id}> ({after.author.id}) [{after.channel.mention}] [[Jump]({after.jump_url})]", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(after.author)}", icon_url=f"{after.author.display_avatar.url}")
        embed.add_field(
            name=f"❌ Before on <t:{after.created_at.astimezone().strftime('%s')}:f>",
            value=f">>> {before_content}",
            inline=True
        )
        embed.add_field(
            name=f"⭕ After on <t:{after.edited_at.astimezone().strftime('%s')}:f>",
            value=f">>> {after_content}",
            inline=True
        )

        msg = (
            "📝 **Message edit**: \n"
            f"from {self.bot.escape_message(after.author.name)} "
            f"({after.author.id}), in {after.channel.mention}:\n"
            f"```{before_content}``` → ```{after_content}```\n"
            f"Jump: <{after.jump_url}>"
        )

        # If resulting message is too long, upload to hastebin
        if len(msg) > 2000:
            haste_url = await self.bot.haste(msg)
            msg = f"📝 **Message Edit**\nToo long: <{haste_url}>"
            await log_channel.send(msg)
        else:
            await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.channel.id not in config.spy_channels or message.author.bot:
            return

        log_channel = self.bot.get_channel(config.log_channel)
        
        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.dark_gray(), title="🗑️ Message Delete", description=f"<@{message.author.id}> ({message.author.id}) [{message.channel.mention}]", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(message.author)}", icon_url=f"{message.author.display_avatar.url}")
        embed.add_field(
            name=f"🧾 Sent on <t:{message.created_at.astimezone().strftime('%s')}:f>:",
            value=f">>> {message.clean_content}",
            inline=True
        )

        msg = (
            "🗑️ **Message delete**: \n"
            f"from {self.bot.escape_message(message.author.name)} "
            f"({message.author.id}), in {message.channel.mention}:\n"
            f"`{message.clean_content}`"
        )

        # If resulting message is too long, upload to hastebin
        if len(msg) > 2000:
            haste_url = await self.bot.haste(msg)
            msg = f"🗑️ **Message Delete**\nToo long: <{haste_url}>"
            await log_channel.send(msg)
        else:
            await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()

        if member.guild.id not in config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(config.log_channel)
        escaped_name = self.bot.escape_message(member)
        
        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.darker_gray(), title="📥 User Left", description=f"<@{member.id}> ({member.id})", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{escaped_name}", icon_url=f"{member.display_avatar.url}")
        embed.set_thumbnail(url=f"{member.display_avatar.url}")
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
            inline=True
        )
        embed.add_field(
            name="⏱️ Account joined:",
            value=f"<t:{member.joined_at.astimezone().strftime('%s')}:f>\n<t:{member.joined_at.astimezone().strftime('%s')}:R>",
            inline=True
        )

        await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()

        if guild.id not in config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(config.modlog_channel)
        escaped_name = self.bot.escape_message(member)

        msg = (
            f"⛔ **Ban**: {escaped_name} ("
            f"{member.id})"
        )
        await log_channel.send(msg)

    @Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.bot.wait_until_ready()

        if guild.id not in config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(config.modlog_channel)
        escaped_name = self.bot.escape_message(member)

        msg = (
            f"⚠️ **Unban**: {escaped_name} ("
            f"{member.id})"
        )
        # if user.id in self.bot.timebans:
        #     msg += "\nTimeban removed."
        #     self.bot.timebans.pop(user.id)
        #     with open("data/timebans.json", "r") as f:
        #         timebans = json.load(f)
        #     if user.id in timebans:
        #         timebans.pop(user.id)
        #         with open("data/timebans.json", "w") as f:
        #             json.dump(timebans, f)
        await log_channel.send(msg)

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()

        if member_after.guild.id not in config.guild_whitelist:
            return

        updated = False
        # initialize embed
        embed = discord.Embed(
            color=discord.Colour.from_str("#0000FF"), title="ℹ️ Member Update", description=f"{member_after.mention} ({self.bot.escape_message(member_after.id)}", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(member_after)}", icon_url=f"{member_after.display_avatar.url}")
        
        log_channel = self.bot.get_channel(config.log_channel)
        if member_before.roles != member_after.roles:
            # role removal code
            role_removal = []
            for index, role in enumerate(member_before.roles):
                if role not in member_after.roles:
                    role_removal.append(role)
            # role addition code
            role_addition = []
            for index, role in enumerate(member_after.roles):
                if role not in member_before.roles:
                    role_addition.append(role)

            if len(role_addition) != 0 or len(role_removal) != 0:
                updated = True
                roles = []
                for role in role_removal:
                    roles.append("_~~" + role.name + "~~_")
                for role in role_addition:
                    roles.append("__**" + role.name + "**__")
                for index, role in enumerate(member_after.roles):
                    if role.name == "@everyone":
                        continue
                    if role not in role_removal and role not in role_addition:
                        roles.append(role.name)
                rolelist = "\n".join(roles)
                embed.add_field(
                    name=f"🎨 Role Change",
                    value=f'{rolelist}',
                    inline=False
                )

        if member_before.name != member_after.name:
            updated = True
            embed.add_field(
                name=f"📝  Username Change",
                value=f'❌ {self.bot.escape_message(member_before)}\n⬇️\n⭕ {self.bot.escape_message(member_after)}',
                inline=False
            )
        if member_before.nick != member_after.nick:
            updated = True
            if not member_before.nick:
                fname = "🏷 Nickname Added"
            elif not member_after.nick:
                fname =  "🏷 Nickname Removed"
            else:
                fname = "🏷 Nickname Changed"
            embed.add_field(
                name=f"{fname}",
                value=f'❌ {self.bot.escape_message(member_before.nick)}\n⬇️\n⭕ {self.bot.escape_message(member_after.nick)}',
                inline=False
            )
        if updated:
            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))
