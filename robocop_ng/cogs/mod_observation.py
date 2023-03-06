from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
import datetime
from helpers.checks import check_if_staff


class ModObserve(Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.raidmode = False

    @Cog.listener()
    async def on_member_join(self, member):
        ts = datetime.datetime.now(datetime.timezone.utc)
        cutoff_ts = ts - datetime.timedelta(hours=24)
        if member.created_at >= cutoff_ts or self.bot.raidmode = True:
            staff_channel = config.staff_channel
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
            if self.bot.raidmode == True:
                rmstr = " "
            else:
                rmstr = "not"
            embed.add_field(
                name="🚨 Raid mode...",
                value=f"is {rmstr} enabled.",
                inline=False
            )
            embeds.append(embed)
            await member.guild.get_channel(staff_channel).send(embed=embeds)
        

async def setup(bot):
    await bot.add_cog(ModObserve(bot))
