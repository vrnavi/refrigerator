import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import config
import datetime
import asyncio
from unidecode import unidecode
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class NameCheck(Cog):
    """
    Keeping names readable.
    """

    def __init__(self, bot):
        self.bot = bot
        self.readablereq = 1

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def decancer(self, ctx, target: discord.Member):
        oldname = target.display_name
        newname = unidecode(target.display_name)
        if not newname:
            newname = "Unreadable Name"
        await target.edit(nick=target.display_name, reason="Namecheck")
        return await ctx.reply(
            content=f"Successfully decancered **{oldname}** to  `{newname}`.",
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def dehoist(self, ctx, target: discord.Member):
        oldname = target.display_name
        await target.edit(nick="᲼" + target.display_name, reason="Namecheck")
        return await ctx.reply(
            content=f"Successfully dehoisted **{oldname}**.", mention_author=False
        )

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not get_config(member.guild.id, "misc", "autoreadable_enable"):
            return

        # Hoist
        if member.display_name[:1] in ("!", "-", ".", "(", ")", ":"):
            await member.edit(
                nick="᲼" + member.display_name, reason="Automatic Namecheck"
            )

        # Non-Alphanumeric
        readable = len([b for b in member.display_name if b.isalnum()])
        if readable < self.readablereq:
            newname = unidecode(member.display_name)
            if not newname:
                newname = "Unreadable Name"
            await member.edit(nick=newname, reason="Automatic Namecheck")

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()
        if not get_config(member_after.guild.id, "misc", "autoreadable_enable"):
            return

        # Hoist
        if member_after.display_name[:1] in ("!", "-", ".", "(", ")", ":"):
            await member_after.edit(
                nick="᲼" + member_after.display_name, reason="Automatic Namecheck"
            )

        # Non-Alphanumeric
        readable = len([b for b in member_after.display_name if b.isalnum()])
        if readable < self.readablereq:
            newname = unidecode(member_after.display_name)
            if not newname:
                newname = "Unreadable Name"
            await member_after.edit(nick=newname, reason="Automatic Namecheck")


async def setup(bot):
    await bot.add_cog(NameCheck(bot))
