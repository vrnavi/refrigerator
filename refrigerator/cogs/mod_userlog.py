import revolt
from revolt.ext import commands
import config
import json
from datetime import datetime, timezone
from helpers.checks import check_if_staff, check_only_server
from helpers.userlogs import get_userlog, set_userlog, userlog_event_types
from helpers.colors import colors
from helpers.messageutils import message_to_url, get_dm_channel


class ModUserlog(commands.Cog):
    def __init__(self, bot: revolt.Client):
        self.bot = bot

    def get_userlog_embed_for_id(
        self, gid: int, uid: str, name: str, own: bool = False, event=""
    ):
        own_note = " Congratulations." if own else ""
        wanted_events = ["warns", "kicks", "bans"]
        if not own:
            wanted_events = ["tosses"] + wanted_events
        if event and not isinstance(event, list):
            wanted_events = [event]
        embed = revolt.embed.SendableEmbed(colour=colors.dark_red, description="")
        embed.title = f"Logs for {name}"
        userlog = get_userlog(gid)

        if uid not in userlog:
            embed.description = f"No records found.{own_note}"
            embed.colour = colors.green
            return embed

        for event_type in wanted_events:
            if event_type in userlog[uid] and userlog[uid][event_type]:
                event_name = userlog_event_types[event_type]
                contents = ""
                for idx, event in enumerate(userlog[uid][event_type]):
                    issuer = (
                        ""
                        if own
                        else f"__Issuer:__ <@{event['issuer_id']}> "
                        f"({event['issuer_id']})\n"
                    )
                    timestamp = datetime.strptime(
                        event["timestamp"], "%Y-%m-%d %H:%M:%S"
                    ).strftime("%s")
                    contents += (
                        f"\n`{event_name} {idx + 1}` <t:{timestamp}:R> on <t:{timestamp}:f>\n"
                        + issuer
                        + f"__Reason:__ {event['reason']}\n"
                    )
                if len(contents) != 0:
                    embed.description += (
                        f"**{event_type.capitalize()}**\n {contents}\n",
                    )

        if not own and "watch" in userlog[uid]:
            if userlog[uid]["watch"]["state"]:
                watch_state = ""
            else:
                watch_state = "not "
                embed.colour = colors.orange
            embed.description += f"User is {watch_state}under watch."

        if embed.description == "":
            embed.description = f"No logs recorded.{own_note}"
            embed.colour = colors.green
        return embed

    def clear_event_from_id(self, uid: str, event_type):
        userlog = get_userlog()
        if uid not in userlog:
            return f"<@{uid}> has no {event_type}!"
        event_count = len(userlog[uid][event_type])
        if not event_count:
            return f"<@{uid}> has no {event_type}!"
        userlog[uid][event_type] = []
        set_userlog(json.dumps(userlog))
        return f"<@{uid}> no longer has any {event_type}!"

    def delete_event_from_id(self, uid: str, idx: int, event_type):
        userlog = get_userlog()
        if uid not in userlog:
            return f"<@{uid}> has no {event_type}!"
        event_count = len(userlog[uid][event_type])
        if not event_count:
            return f"<@{uid}> has no {event_type}!"
        if idx > event_count:
            return "Index is higher than " f"count ({event_count})!"
        if idx < 1:
            return "Index is below 1!"
        event = userlog[uid][event_type][idx - 1]
        event_name = userlog_event_types[event_type]
        embed = revolt.embed.SendableEmbed(
            color=colors.dark_red,
            title=f"{event_name} {idx} on " f"{event['timestamp']}",
            description=f"Issuer: {event['issuer_name']}\n"
            f"Reason: {event['reason']}",
        )
        del userlog[uid][event_type][idx - 1]
        set_userlog(json.dumps(userlog))
        return embed

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["events"])
    async def eventtypes(self, ctx: commands.Context):
        """[S] Lists available event types."""
        event_list = [f"{et} ({userlog_event_types[et]})" for et in userlog_event_types]
        event_text = "Available events:\n``` - " + "\n - ".join(event_list)
        await ctx.send(event_text)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(name="userlog", aliases=["logs"])
    async def userlog_cmd(
        self,
        ctx: commands.Context,
        target: commands.converters.UserConverter = None,
        event="",
    ):
        if not target:
            await ctx.send("You must specify a user to list logs for.")
            return

        """[S] Lists userlog events for a user."""
        if ctx.server.get_member(target.id):
            target = ctx.server.get_member(target.id)
        embed = self.get_userlog_embed_for_id(
            ctx.server.id,
            str(target.id),
            f"{target.original_name}#{target.discriminator}",
            event=event,
        )
        await ctx.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["listnotes", "usernotes"])
    async def notes(
        self, ctx: commands.Context, target: commands.converters.MemberConverter = None
    ):
        if not target:
            await ctx.send("You must specify a user to list notes for.")
            return

        """[S] Lists notes for a user."""
        embed = self.get_userlog_embed_for_id(
            ctx.server.id,
            str(target.id),
            f"{target.original_name}#{target.discriminator}",
            event="notes",
        )
        await ctx.send(embed=embed)

    @commands.check(check_only_server)
    @commands.command(aliases=["mywarns", "mylogs"])
    async def myuserlog(self, ctx: commands.Context):
        """[U] Lists your userlog events (warns, etc)."""
        embed = self.get_userlog_embed_for_id(
            ctx.server.id,
            str(ctx.author.id),
            f"{ctx.author.original_name}#{ctx.author.discriminator}",
            True,
        )
        dm_channel = await get_dm_channel(self.bot, ctx.author)
        await dm_channel.send(embed=embed)

        await ctx.message.add_reaction("📨")
        await ctx.message.reply(
            content="For privacy, your logs have been DMed.", mention=False
        )

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["clearwarns"])
    async def clearevent(
        self,
        ctx: commands.Context,
        target: commands.converters.MemberConverter,
        event="warns",
    ):
        """[S] Clears all events of given type for a user."""
        # target handler
        # In the case of IDs.
        try:
            target = await self.bot.fetch_user(int(target))
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        mlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.server.id]["logs"]["mlog_thread"]
        )
        msg = self.clear_event_from_id(str(target.id), event)
        safe_name = f"{target.original_name}#{target.discriminator}"
        await ctx.send(msg)
        msg = (
            f"🗑 **Cleared {event}**: {ctx.author.mention} cleared"
            f" all {event} events of {target.mention} | "
            f"{safe_name}"
            f"\n🔗 __Jump__: <f{message_to_url(ctx.message)}>"
        )
        await mlog.send(msg)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["delwarn"])
    async def delevent(self, ctx: commands.Context, target, idx: int, event="warns"):
        """[S] Removes a specific event from a user."""
        # target handler
        # In the case of IDs.
        try:
            target = await self.bot.fetch_user(int(target))
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        mlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.server.id]["logs"]["mlog_thread"]
        )
        del_event = self.delete_event_from_id(str(target.id), idx, event)
        event_name = userlog_event_types[event].lower()
        # This is hell.
        if isinstance(del_event, ctx.server):
            await ctx.send(f"{target.mention} has a {event_name} removed!")
            safe_name = f"{target.original_name}#{target.discriminator}"
            msg = (
                f"🗑 **Deleted {event_name}**: "
                f"{ctx.author.mention} removed "
                f"{event_name} {idx} from {target.mention} | {safe_name}"
                f"\n🔗 __Jump__: <{message_to_url(ctx.message)}>"
            )
            await mlog.send(msg, embed=del_event)
        else:
            await ctx.send(del_event)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def fullinfo(
        self, ctx: commands.Context, target: commands.converters.MemberConverter = None
    ):
        """[S] Gets full user info."""
        if not target:
            target = ctx.author

        embeds: list[revolt.SendableEmbed] = []

        if not ctx.server.get_member(target.id):
            # Memberless code.
            color = colors.light_grey
            nickname = ""
        else:
            # Member code.
            target = ctx.server.get_member(target.id)
            nickname = f"\n**Nickname:** `{target.display_name}`"

        embed = revolt.SendableEmbed(
            title=f"Info for {'user' if ctx.server.get_member(target.id) else 'member'} {f'{target.original_name}#{target.discriminator}'}{' [BOT]' if target.bot else ''}",
            description=f"**ID:** `{target.id}`{nickname}",
            icon_url=target.avatar.url if target.avatar is not None else None,
        )

        account_creation = int(target.created_at().astimezone().timestamp())

        embed.description += f"\n**⏰ Account created:** <t:{account_creation}:f>\n<t:{account_creation}:R>"

        if ctx.server.get_member(target.id):
            joined_at = int(target.joined_at.astimezone().timestamp())

            embed.description += (
                f"\n**⏱️ Account joined:** <t:{joined_at}:f> (<t:{joined_at}:R>)"
            )
            embed.description += f"\n**🗃️ Joinscore:** `{sorted(ctx.server.members, key=lambda v: v.joined_at).index(target)+1}` of `{len(ctx.server.members)}`"

            status = ""
            try:
                status = f"{target.status.text}" if target.status.text else ""
            except:
                status = ""

            if status:
                embed.description += f"\n**💭 Status:** `{status}`"

            roles = []
            if target.roles:
                for index, role in enumerate(target.roles):
                    roles.append(role.name)
                    rolelist = ",".join(reversed(roles))
            else:
                rolelist = "None"

            embed.description += f"\n**🎨 Roles:** {rolelist}"
        embeds.append(embed)

        event_types = ["warns", "bans", "kicks", "tosses", "notes"]
        embed = self.get_userlog_embed_for_id(
            ctx.server.id,
            str(target.id),
            f"{target.original_name}#{target.discriminator}",
            event=event_types,
        )
        embeds.append(embed)

        for idx in embeds:
            await ctx.send(embed=idx)


def setup(bot: revolt.Client):
    return ModUserlog(bot)
