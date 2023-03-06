# This Cog contains code from discord-mass-lockdown, which was made by Roadcrosser.
# https://github.com/Roadcrosser/discord-mass-lockdown
from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
from helpers.checks import check_if_staff


class ModAntiRaid(Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.GUILD = bot.get_guild(config.guild_usage)
        bot.AUTHORIZED_ROLE = (
            bot.GUILD.get_role(config.named_roles["journal"]) if bot.GUILD else None
        )
        bot.STAFF_ROLE_ID = config.staff_role_ids[0]
        bot.ANNOUNCE_CHANNEL = config.general_channels[0]
        if bot.ANNOUNCE_CHANNEL != "all":
            bot.ANNOUNCE_CHANNEL = (
                bot.GUILD.get_channel(bot.ANNOUNCE_CHANNEL) if bot.GUILD else None
            )
        bot.LOCKDOWN_ANNOUNCEMENT = "All public channels are temporarily restricted."
        bot.UNLOCKDOWN_ANNOUNCEMENT = "All public channels are no longer restricted."
        bot.MENTION_THRESHOLD = config.mention_threshold
        bot.STAFF_CHANNEL = (
            bot.GUILD.get_channel(config.staff_channel) if bot.GUILD else None
        )
        bot.RECENT_JOIN_THRESHOLD = config.recent_join_threshold
        bot.LOCKED_DOWN_CHANNELS = set()
        bot.ANNOUNCE_MESSAGES = {}
        bot.AUTOLOCKDOWN_IN_PROGRESS = False
        bot.RECENT_MEMBER_CACHE = None
        if bot.RECENT_JOIN_THRESHOLD > 0:
            bot.RECENT_MEMBER_CACHE = bot.GUILD.members
            self.cull_recent_member_cache()

    def cull_recent_member_cache(ts=None):
        if bot.RECENT_JOIN_THRESHOLD <= 0:
            return

        if not ts:
            ts = datetime.datetime.utcnow()

        cutoff_ts = ts - datetime.timedelta(seconds=bot.RECENT_JOIN_THRESHOLD)

        bot.RECENT_MEMBER_CACHE = [
            m
            for m in bot.RECENT_MEMBER_CACHE
            # It's easier to cull members who leave here than on leave
            if bot.GUILD.get_member(m.id)
            # Cutoff is inclusive
            and m.joined_at >= cutoff_ts
        ]
        
    def is_public_channel(self, channel):
        # Definition of a public channel:
        # (Will revert to None)
        #
        # @everyone role
        #    - Read messages: None/True
        #    - Send messages: None/True
        #
        # Authorized role
        #    - Read messages: None/True
        #    - Send messages: None/True

        default_role_override = channel.overwrites_for(channel.guild.default_role)
        authorized_role_override = channel.overwrites_for(bot.AUTHORIZED_ROLE)

        return all(
            [
                i in [None, True]
                for i in [
                    default_role_override.read_messages,
                    default_role_override.send_messages,
                    authorized_role_override.read_messages,
                    authorized_role_override.send_messages,
                ]
            ]
        )
        
    def get_public_channels(self):
        return [
            c
            for c in bot.GUILD.text_channels
            if c.permissions_for(bot.GUILD.me).manage_channels and self.is_public_channel(c)
        ]
        
    def parse_channel_list(self, args):
        if not args:
            return []

        arg_channels = args.split()
        affected_channels = set()

        for c in arg_channels:

            c = c.lower()
            try:
                c = int(c.strip("<#>"))
            except:
                pass
            affected_channels.add(c)

        return [
            c
            for c in bot.GUILD.channels
            if (c.id in affected_channels)
            or (c.name in affected_channels)
            and not isinstance(c, discord.TextChannel)
        ]
        
    async def announce_lockdown(self, channel_list, lockdown):
        if not bot.ANNOUNCE_CHANNEL:
            return

        to_announce = channel_list
        if bot.ANNOUNCE_CHANNEL != "all":
            to_announce = [bot.ANNOUNCE_CHANNEL]

        for c in to_announce:
            if not c.permissions_for(c.guild.me).send_messages:
                continue

            message = bot.LOCKDOWN_ANNOUNCEMENT if lockdown else bot.UNLOCKDOWN_ANNOUNCEMENT

            if message:
                msg = await c.send(message)
                if c.permissions_for(c.guild.me).manage_messages and lockdown:
                    try:
                        await msg.pin(reason="[Mass Lockdown Announcement]")
                        bot.ANNOUNCE_MESSAGES[c.id] = msg
                    except:
                        pass

            if c.permissions_for(c.guild.me).manage_messages and not lockdown:
                pinned_msg = bot.ANNOUNCE_MESSAGES.pop(c.id, None)
                if pinned_msg:
                    try:
                        await pinned_msg.unpin(reason="[Mass Unlockdown Announcement]")
                    except:
                        pass

    async def perform_lockdown(self, channel_list, lockdown):
        success_channels = []
        fail_channels = []

        for c in channel_list:
            default_role_override = c.overwrites_for(c.guild.default_role)
            authorized_role_override = c.overwrites_for(bot.AUTHORIZED_ROLE)
            bot_override = c.overwrites_for(c.guild.me)

            if lockdown:
                default_role_override.send_messages = False
                authorized_role_override.send_messages = True
                bot_override.send_messages = True
            else:
                default_role_override.send_messages = None
                authorized_role_override.send_messages = None
                bot_override.send_messages = None

            try:
                for i, u in [
                    (c.guild.default_role, default_role_override),
                    (bot.AUTHORIZED_ROLE, authorized_role_override),
                    (c.guild.me, bot_override),
                ]:
                    if u.is_empty():
                        u = None

                    await c.set_permissions(
                        i,
                        overwrite=u,
                        reason="[Mass {}ockdown]".format("L" if lockdown else "Unl"),
                    )

                success_channels.append(c)

                if lockdown:
                    bot.LOCKED_DOWN_CHANNELS.add(c.id)
                elif c.id in bot.LOCKED_DOWN_CHANNELS:
                    bot.LOCKED_DOWN_CHANNELS.remove(c.id)
            except:
                fail_channels.append(c.mention)

        ret = "{}ocked down the following channels:\n```\n{}\n```".format(
            "L" if lockdown else "Unl", "\n".join([str(c.id) for c in success_channels])
        )

        if fail_channels:
            ret += "\nFailed to {}ockdown the following channels: {}".format(
                "l" if lockdown else "unl", " ".join(fail_channels)
            )

        if success_channels:
            await self.announce_lockdown(success_channels, lockdown)

        return ret
        
    async def execute_auto_lockdown(message):
        bot.AUTOLOCKDOWN_IN_PROGRESS = True

        channel_list = self.get_public_channels()

        staff_channel_accessible = (
            bot.STAFF_CHANNEL
            and bot.STAFF_CHANNEL.permissions_for(bot.STAFF_CHANNEL.guild.me).send_messages
        )

        if staff_channel_accessible:
            staff_announce_msg = f"{message.author.mention} ({message.author.id}) mentioned `{len(message.mentions)}` members in {message.channel.mention}."

            if bot.RECENT_JOIN_THRESHOLD > 0:
                self.cull_recent_member_cache(message.created_at)
                staff_announce_msg += (
                    f"\nMembers who joined in the last {bot.RECENT_JOIN_THRESHOLD} seconds: "
                    + " ".join([m.mention for m in bot.RECENT_MEMBER_CACHE])
                )

            staff_announce_msg += (
                "\n\nNow locking down the following channels: "
                + " ".join([c.mention for c in channel_list])
            )

            await bot.STAFF_CHANNEL.send(staff_announce_msg)

        ret = await self.perform_lockdown(channel_list, True)

        if staff_channel_accessible:
            await bot.STAFF_CHANNEL.send(ret)    
        
    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["ml"])
    async def lockdown(self, message, *, args = ""):
        channel_list = parse_channel_list(args)
        if not channel_list:
            channel_list = self.get_public_channels()

        async with message.channel.typing():
            ret = await self.perform_lockdown(channel_list, True)
        await message.channel.send(ret)
        
    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["ul"])
    async def unlockdown(self, message, *, args = ""):
        channel_list = parse_channel_list(args)
        if not channel_list:
            channel_list = [
                c
                for c in bot.GUILD.text_channels
                if c.permissions_for(bot.GUILD.me).manage_channels
                and c.id in bot.LOCKED_DOWN_CHANNELS
            ]
            if not channel_list:
                await message.channel.send(
                    "Error: No locked down channels were cached (or had no permissions to modify them).\nPlease specify list of IDs to unlockdown."
                )
                return

        async with message.channel.typing():
            ret = await self.perform_lockdown(channel_list, False)

        bot.AUTOLOCKDOWN_IN_PROGRESS = False
        await message.channel.send(ret)
        
    @Cog.listener()
    async def on_message(message):
        if (
            not bot.ready
            or message.author.bot
            or not message.content
            or not message.guild
            or message.guild.id != bot.GUILD.id
        ):
            return

        if (
            # Check auto-lockdown is enabled
            bot.MENTION_THRESHOLD > 0
            # Check auto-lockdown not already in progress
            and not bot.AUTOLOCKDOWN_IN_PROGRESS
            # Check channel is public
            and self.is_public_channel(message.channel)
            # Check for no roles (@everyone counts as a role internally)
            and len(message.author.roles) == 1
            # Check that mention count exceeds threshold
            and len(message.mentions) >= bot.MENTION_THRESHOLD
        ):
            await self.execute_auto_lockdown(message)
        
    @Cog.listener()
    async def on_member_join(member):
        bot.RECENT_MEMBER_CACHE.append(member)
        self.cull_recent_member_cache()


async def setup(bot):
    await bot.add_cog(ModAntiRaid(bot))
