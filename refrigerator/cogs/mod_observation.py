from revolt.ext import commands
import revolt
import config
import discord
import datetime
import asyncio
from helpers.checks import check_if_staff, check_only_server
from helpers.sv_config import get_config
from helpers.embeds import SendableFieldedEmbedBuilder
from helpers.colors import colors


class ModObserve(commands.Cog):
    """
    A tool to help moderators keep track of potential problem users.
    """

    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot
        self.raidmode_list = []

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def raidmode(self, ctx: commands.Context, args: str):
        if not args:
            if ctx.server.id in self.raidmode_list:
                await ctx.message.reply("Raid mode is currently `🟢 ON`.")
            else:
                await ctx.message.reply("Raid mode is currently `🔴 OFF`.")
            return
        if args == "on":
            if ctx.server.id not in self.raidmode_list:
                self.raidmode_list.append(ctx.server.id)
                await ctx.message.reply("Raid mode is now `🟢 ON`.")
            else:
                await ctx.message.reply("Raid mode is already `🟢 ON`!")
            return
        if args == "off":
            if ctx.server.id in self.raidmode_list:
                self.raidmode_list.remove(ctx.guild.id)
                await ctx.message.reply("Raid mode is now `🔴 OFF`.")
            else:
                await ctx.message.reply("Raid mode is already  `🔴 OFF`!")
            return
        else:
            await ctx.message.reply("Incorrect arguments. Use `on` or `off`.")
            return


    async def on_member_join(self, member: revolt.Member):
        if not get_config(member.server.id, "staff", "staff_channel"):
            return
        ts = datetime.datetime.now(datetime.timezone.utc)
        cutoff_ts = ts - datetime.timedelta(hours=24)
        if member.created_at >= cutoff_ts or member.server.id in self.raidmode_list:
            if member.server.id in self.raidmode:
                rmstr = "`🟢 ON`"
            else:
                rmstr = "`🔴 OFF`"

            embed = SendableFieldedEmbedBuilder(
                title="📥 User Joined",
                description=f"{member.mention} ({member.id})",
                color=colors.lighter_grey,
                fields=[
                    ("📅 Account created:", f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>"),
                    ("🚨 Raid mode...", f"is currently {rmstr}."),
                    ("🔍 First message:", "Currently watching..."),
                ]
            )

            staff_channel: revolt.TextChannel = await member.server.get_channel(
                get_config(member.server.id, "staff", "staff_channel")
            )

            callout = await staff_channel.send(embed=embed)

            try:
                msg = await self.bot.wait_for("message_create", timeout=7200, check=lambda m: m.author.id == member.id and m.server.id == member.server.id)
                embed.set_field_at(
                    index=2,
                    name="🔍 First message:",
                    value=f"[Sent]({msg.jump_url}) in {msg.channel.mention} on <t:{msg.created_at.astimezone().strftime('%s')}:f> (<t:{msg.created_at.astimezone().strftime('%s')}:R>):\n```{msg.clean_content}```",
                )
            except asyncio.TimeoutError:
                embed.set_field_at(
                    index=2,
                    name="🔍 First message:",
                    value=f"This user did not send a message within `2 hours`.",
                )
            await callout.edit(embed=embed.build())


def setup(bot):
    return ModObserve(bot)
