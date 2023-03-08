import discord
from discord.ext import commands
from discord.ext.commands import Cog
import config
import json
from datetime import datetime, timezone
from helpers.checks import check_if_staff
from helpers.userlogs import get_userlog, set_userlog, userlog_event_types


class ModUserlog(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_userlog_embed_for_id(
        self, uid: str, name: str, own: bool = False, event=""
    ):
        own_note = " Congratulations." if own else ""
        wanted_events = ["warns", "bans", "kicks", "mutes"]
        if event and not isinstance(event, list):
            wanted_events = [event]
        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_author(name=f"Userlog for {name}")
        userlog = get_userlog()

        if uid not in userlog:
            embed.description = f"No records found.{own_note}"
            embed.color = discord.Color.green()
            return embed

        for event_type in wanted_events:
            if event_type in userlog[uid] and userlog[uid][event_type]:
                event_name = userlog_event_types[event_type]
                for idx, event in enumerate(userlog[uid][event_type]):
                    issuer = (
                        ""
                        if own
                        else f"__Issuer:__ <@{event['issuer_id']}> "
                        f"({event['issuer_id']})\n"
                    )
                    timestamp = datetime.strptime(event['timestamp'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone().strftime("%s")
                    embed.add_field(
                        name=f"{event_name} {idx + 1}: <t:{timestamp}:f> (<t:{timestamp}:R>)",
                        value=issuer + f"__Reason:__ {event['reason']}",
                        inline=False,
                    )

        if not own and "watch" in userlog[uid]:
            if userlog[uid]["watch"]:
                watch_state = "" 
            else:
                watch_state = "not "
                embed.color = discord.Color.orange()
            embed.set_footer(text=f"User is {watch_state}under watch.")

        if not embed.fields:
            embed.description = f"There are none!{own_note}"
            embed.color = discord.Color.green()
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
        embed = discord.Embed(
            color=discord.Color.dark_red(),
            title=f"{event_name} {idx} on " f"{event['timestamp']}",
            description=f"Issuer: {event['issuer_name']}\n"
            f"Reason: {event['reason']}",
        )
        del userlog[uid][event_type][idx - 1]
        set_userlog(json.dumps(userlog))
        return embed

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["events"])
    async def eventtypes(self, ctx):
        """[S] Lists available event types."""
        event_list = [f"{et} ({userlog_event_types[et]})" for et in userlog_event_types]
        event_text = "Available events:\n``` - " + "\n - ".join(event_list) + "```"
        await ctx.send(event_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(
        name="userlog", aliases=["logs"]
    )
    async def userlog_cmd(self, ctx, target, event=""):
        """[S] Lists userlog events for a user."""
        # In the case of IDs.
        try:
            target_id = int(target)
            user = await self.bot.fetch_user(target_id)
            embed = self.get_userlog_embed_for_id(target, str(user.display_name), event=event)
        # In the case of mentions.
        except ValueError:
            user = await self.bot.fetch_user(target[2:-1])
            embed = self.get_userlog_embed_for_id(str(user.id), str(user.display_name), event=event)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["listnotes", "usernotes"])
    async def notes(self, ctx, target: discord.Member):
        """[S] Lists notes for a user."""
        embed = self.get_userlog_embed_for_id(
            str(target.id), str(target), event="notes"
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["mywarns", "mylogs",])
    async def myuserlog(self, ctx):
        """[U] Lists your userlog events (warns, etc)."""
        embed = self.get_userlog_embed_for_id(str(ctx.author.id), str(ctx.author), True)
        try:
            await ctx.author.send(embed=embed)
        except:
            await ctx.reply(content="Unable to send. Your DMs may be closed.", mention_author=False)
            return
        await ctx.add_reaction("📨")
        await ctx.reply(content="For privacy, your logs have been DMed.", mention_author=False)

#    LOL REDUNDANT.
#    @commands.guild_only()
#    @commands.check(check_if_staff)
#    @commands.command(aliases=["listwarnsid"])
#    async def userlogid(self, ctx, target: int):
#        """[S] Lists the userlog events for a user by ID."""
#        embed = self.get_userlog_embed_for_id(str(target), str(target))
#        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clearwarns"])
    async def clearevent(self, ctx, target: discord.Member, event="warns"):
        """[S] Clears all events of given type for a user."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        msg = self.clear_event_from_id(str(target.id), event)
        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        await ctx.send(msg)
        msg = (
            f"🗑 **Cleared {event}**: {ctx.author.mention} cleared"
            f" all {event} events of {target.mention} | "
            f"{safe_name}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        await log_channel.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clearwarnsid"])
    async def cleareventid(self, ctx, target: int, event="warns"):
        """[S] Clears all events of given type for an ID."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        msg = self.clear_event_from_id(str(target), event)
        await ctx.send(msg)
        msg = (
            f"🗑 **Cleared {event}**: {ctx.author.mention} cleared"
            f" all {event} events of <@{target}> "
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        await log_channel.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["delwarn"])
    async def delevent(self, ctx, target: discord.Member, idx: int, event="warns"):
        """[S] Removes a specific event from a user."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        del_event = self.delete_event_from_id(str(target.id), idx, event)
        event_name = userlog_event_types[event].lower()
        # This is hell.
        if isinstance(del_event, discord.Embed):
            await ctx.send(f"{target.mention} has a {event_name} removed!")
            safe_name = await commands.clean_content(escape_markdown=True).convert(
                ctx, str(target)
            )
            msg = (
                f"🗑 **Deleted {event_name}**: "
                f"{ctx.author.mention} removed "
                f"{event_name} {idx} from {target.mention} | {safe_name}"
                f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
            )
            await log_channel.send(msg, embed=del_event)
        else:
            await ctx.send(del_event)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["delwarnid"])
    async def deleventid(self, ctx, target: int, idx: int, event="warns"):
        """[S] Removes a specific event from an ID."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        del_event = self.delete_event_from_id(str(target), idx, event)
        event_name = userlog_event_types[event].lower()
        # This is hell.
        if isinstance(del_event, discord.Embed):
            await ctx.send(f"<@{target}> has a {event_name} removed!")
            msg = (
                f"🗑 **Deleted {event_name}**: "
                f"{ctx.author.mention} removed "
                f"{event_name} {idx} from <@{target}> "
                f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
            )
            await log_channel.send(msg, embed=del_event)
        else:
            await ctx.send(del_event)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def userinfo(self, ctx, *, user: discord.Member):
        """[S] Gets user info."""
        role = user.top_role.name
        if role == "@everyone":
            role = "@ everyone"

        event_types = ["warns", "bans", "kicks", "mutes", "notes"]
        embed = self.get_userlog_embed_for_id(
            str(user.id), str(user), event=event_types
        )

        user_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, user.name
        )
        display_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, user.display_name
        )

        await ctx.send(
            f"user = {user_name}\n"
            f"id = {user.id}\n"
            f"avatar = {user.avatar_url}\n"
            f"bot = {user.bot}\n"
            f"created_at = {user.created_at}\n"
            f"display_name = {display_name}\n"
            f"joined_at = {user.joined_at}\n"
            f"color = {user.colour}\n"
            f"top_role = {role}\n",
            embed=embed,
        )


async def setup(bot):
    await bot.add_cog(ModUserlog(bot))
