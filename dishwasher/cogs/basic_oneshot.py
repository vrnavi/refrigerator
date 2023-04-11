import config
import discord
import datetime
from discord.ext import commands
from discord.ext.commands import Cog


class BasicOneShot(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    async def journalcount(self, ctx):
        """[O] Prints the Strange Journal count of the server."""
        community = ctx.guild.get_role(config.named_roles["journal"])
        await ctx.send(
            f"{ctx.guild.name} has {len(community.members)} Strange Journal members!"
        )

    @commands.guild_only()
    @commands.command(hidden=True, aliases=["renavi"])
    async def ren(self, ctx):
        """[U] What does Dishwasher think about ren?"""
        await ctx.send("HELP! HELP! HELP!")

    @commands.guild_only()
    @commands.command()
    async def staff(self, ctx):
        """[U] Shows currently active staff."""
        staff_role = ctx.guild.get_role(config.staff_role_ids[0])
        embed = discord.Embed(
            color=staff_role.color,
            title="🛠️ Staff List",
            description=f"Voting requirement is `{int(len(staff_role.members)/2//1+1)}`.",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text="Dishwasher")
        online = []
        away = []
        dnd = []
        offline = []
        for m in staff_role.members:
            u = f"{m.mention}"
            if m.is_on_mobile():
                u = f"{m.mention} 📱"
            if m.raw_status == "online":
                online.append(u)
            elif m.raw_status == "offline":
                offline.append(u)
            elif m.raw_status == "dnd":
                dnd.append(u)
            elif m.raw_status == "idle":
                away.append(u)
        if online:
            embed.add_field(
                name=f"🟢 Online [`{len(online)}`/`{len(staff_role.members)}`]",
                value=f"{','.join(online)}",
                inline=False,
            )
        if away:
            embed.add_field(
                name=f"🟡 Idle [`{len(away)}`/`{len(staff_role.members)}`]",
                value=f"{','.join(away)}",
                inline=False,
            )
        if dnd:
            embed.add_field(
                name=f"🔴 Do Not Disturb [`{len(dnd)}`/`{len(staff_role.members)}`]",
                value=f"{','.join(dnd)}",
                inline=False,
            )
        if offline:
            embed.add_field(
                name=f"⚫ Offline [`{len(offline)}`/`{len(staff_role.members)}`]",
                value=f"{','.join(offline)}",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(BasicOneShot(bot))
