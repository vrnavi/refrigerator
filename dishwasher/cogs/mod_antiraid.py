# This Cog contains code from discord-mass-lockdown, which was made by Roadcrosser.
# https://github.com/Roadcrosser/discord-mass-lockdown
from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
import datetime
from helpers.checks import check_if_staff


class ModAntiRaid(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.locked_channels = {}
        self.announce_msg = {}
        self.in_progress = {}
        self.mem_cache = {}

    def cull_recent_member_cache(self, guild, ts=None):
        if config.guild_configs[guild.id]["antiraid"]["join_threshold"] <= 0:
            return

        if not ts:
            ts = datetime.datetime.now(datetime.timezone.utc)

        cutoff_ts = ts - datetime.timedelta(
            seconds=config.guild_configs[guild.id]["antiraid"]["join_threshold"]
        )

        self.mem_cache = [
            m
            for m in self.mem_cache[guild.id]
            # It's easier to cull members who leave here than on leave
            # ^ True!
            if guild.get_member(m.id)
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

        # Catches threads.
        if not isinstance(channel, discord.TextChannel):
            return False

        default_role_override = channel.overwrites_for(channel.guild.default_role)

        return all(
            [
                i in [None, True]
                for i in [
                    default_role_override.read_messages,
                    default_role_override.send_messages,
                ]
            ]
        )

    def get_public_channels(self, guild):
        return [
            c
            for c in guild.text_channels
            if c.permissions_for(self.guild.me).manage_channels
            and self.is_public_channel(c)
        ]

    def parse_channel_list(self, guild, args):
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
            for c in guild.channels
            if (c.id in affected_channels)
            or (c.name in affected_channels)
            and not isinstance(c, discord.TextChannel)
        ]

    async def announce_lockdown(self, channel_list, lockdown):
        guild = channel_list[0].guild

        if not config.guild_configs[guild.id]["antiraid"]["announce_channels"]:
            return

        to_announce = channel_list
        if config.guild_configs[guild.id]["antiraid"]["announce_channels"] != "all":
            to_announce = []
            for c in config.guild_configs[guild.id]["antiraid"]["announce_channels"]:
                to_announce.append(c)

        for c in to_announce:
            if not c.permissions_for(c.guild.me).send_messages:
                continue

            message = (
                "All public channels are temporarily restricted."
                if lockdown
                else "All public channels are no longer restricted."
            )

            if message:
                msg = await c.send(message)
                if c.permissions_for(c.guild.me).manage_messages and lockdown:
                    try:
                        await msg.pin(reason="[Mass Lockdown Announcement]")
                        self.announce_msg[guild.id][c.id] = msg
                    except:
                        pass

            if c.permissions_for(c.guild.me).manage_messages and not lockdown:
                pinned_msg = self.announce_msg[guild.id].pop(c.id, None)
                if pinned_msg:
                    try:
                        await pinned_msg.unpin(reason="[Mass Unlockdown Announcement]")
                    except:
                        pass

    async def perform_lockdown(self, channel_list, lockdown):
        success_channels = []
        fail_channels = []
        authorized_role_overrides = []

        try:
            allowed_roles = [
                r
                for r in config.guild_configs[channel_list[0].guild.id]["misc"][
                    "authorized_roles"
                ]
            ]
        except:
            allowed_roles = None

        for c in channel_list:
            default_role_override = c.overwrites_for(c.guild.default_role)
            for o in allowed_roles:
                authorized_role_overrides.append(c.overwrites_for(c.guild.get_role(o)))
            bot_override = c.overwrites_for(c.guild.me)

            if lockdown:
                default_role_override.send_messages = False
                bot_override.send_messages = True
                for o in authorized_role_overrides:
                    o.send_messages = True
            else:
                default_role_override.send_messages = None
                bot_override.send_messages = None
                for o in authorized_role_overrides:
                    o.send_messages = None

            overrides = [
                (c.guild.default_role, default_role_override),
                (c.guild.me, bot_override),
            ]
            for r, o in zip(allowed_roles, authorized_role_overrides):
                overrides.append((r, o))

            try:
                for i, u in overrides:
                    await c.set_permissions(
                        i,
                        overwrite=u,
                        reason="[Mass {}ockdown]".format("L" if lockdown else "Unl"),
                    )

                success_channels.append(c)

                if lockdown:
                    self.locked_channels[channel_list[0].guild.id].append(c.id)
                elif c.id in self.locked_channels[channel_list[0].guild.id]:
                    self.locked_channels[channel_list[0].guild.id].remove(c.id)
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

    async def execute_auto_lockdown(self, message):
        self.in_progress[message.guild.id] = True

        channel_list = self.get_public_channels(message.guild)
        staff_channel = message.guild.get_channel(
            config.guild_configs[guild.id]["staff"]["staff_channel"]
        )
        staff_channel_accessible = staff_channel.permissions_for(
            message.guild.me
        ).send_messages

        if staff_channel_accessible:
            staff_announce_msg = f"{message.author.mention} ({message.author.id}) mentioned `{len(message.mentions)}` members in {message.channel.mention}."

            if config.guild_configs[message.guild.id]["antiraid"]["join_threshold"] > 0:
                self.cull_recent_member_cache(message.created_at)
                staff_announce_msg += (
                    f"\nMembers who joined in the last {config.guild_configs[message.guild.id]['antiraid']['join_threshold']} seconds: "
                    + " ".join([m.mention for m in self.mem_cache])
                )

            staff_announce_msg += (
                "\n\nNow locking down the following channels: "
                + " ".join([c.mention for c in channel_list])
            )

            await staff_channel.send(staff_announce_msg)

        ret = await self.perform_lockdown(channel_list, True)

        if staff_channel_accessible:
            await staff_channel.send(ret)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["ml"])
    async def lockdown(self, message, *, args=""):
        if message.guild.id not in config.guild_configs:
            return
        channel_list = self.parse_channel_list(message.guild, args)
        if not channel_list:
            channel_list = self.get_public_channels(message.guild)

        async with message.channel.typing():
            ret = await self.perform_lockdown(channel_list, True)
        await message.channel.send(ret)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["ul"])
    async def unlockdown(self, message, *, args=""):
        if message.guild.id not in config.guild_configs:
            return
        channel_list = self.parse_channel_list(message.guild, args)
        if not channel_list:
            channel_list = [
                c
                for c in message.guild.text_channels
                if c.permissions_for(message.guild.me).manage_channels
                and c.id in self.locked_channels[message.guild.id]
            ]
            if not channel_list:
                await message.channel.send(
                    "Error: No locked down channels were cached (or had no permissions to modify them).\nPlease specify list of IDs to unlockdown."
                )
                return

        async with message.channel.typing():
            ret = await self.perform_lockdown(channel_list, False)

        self.in_progress[message.guild.id] = False
        await message.channel.send(ret)

    @Cog.listener()
    async def on_message(self, message):
        if (
            not self.bot.is_ready()
            or message.author.bot
            or not message.content
            or not message.guild
            or message.guild.id not in config.guild_configs
        ):
            return

        if (
            # Check auto-lockdown is enabled
            config.guild_configs[message.guild.id]["antiraid"]["mention_threshold"] > 0
            # Check auto-lockdown not already in progress
            and not self.in_progress[message.guild.id]
            # Check channel is public
            and self.is_public_channel(message.channel)
            # Check for no roles (@everyone counts as a role internally)
            and len(message.author.roles) == 1
            # Check that mention count exceeds threshold
            and len(message.mentions)
            >= config.guild_configs[message.guild.id]["antiraid"]["mention_threshold"]
        ):
            await self.execute_auto_lockdown(message)

    @Cog.listener()
    async def on_member_join(self, member):
        self.mem_cache[member.guild.id].append(member)
        self.cull_recent_member_cache(member.guild)

    @Cog.listener()
    async def on_ready(self):
        for g in self.bot.guilds:
            if g.id not in config.guild_configs:
                continue
            if config.guild_configs[g.id]["antiraid"]["join_threshold"] > 0:
                self.mem_cache[g.id] = g.members
            self.cull_recent_member_cache(g)
            self.locked_channels[g.id] = []
            self.in_progress[g.id] = False


async def setup(bot):
    await bot.add_cog(ModAntiRaid(bot))
