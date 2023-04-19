from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
import datetime
from helpers.checks import check_if_staff


class ModObserve(Cog):
    def __init__(self, bot):
        self.bot = bot
        raidmode = []

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def raidmode(self, message, args=""):
        if not args:
            if message.guild.id in self.raidmode:
                await message.reply(
                    "Raid mode is currently `🟢 ON`.", mention_author=False
                )
            else:
                await message.reply(
                    "Raid mode is currently `🔴 OFF`.", mention_author=False
                )
            return
        if args == "on":
            if message.guild.id not in self.raidmode:
                self.raidmode.append(message.guild.id)
                await message.reply("Raid mode is now `🟢 ON`.", mention_author=False)
            else:
                await message.reply(
                    "Raid mode is already `🟢 ON`!", mention_author=False
                )
            return
        if args == "off":
            if message.guild.id in self.raidmode:
                self.raidmode.remove(message.guild.id)
                await message.reply("Raid mode is now `🔴 OFF`.", mention_author=False)
            else:
                await message.reply(
                    "Raid mode is already  `🔴 OFF`!", mention_author=False
                )
            return
        else:
            await message.reply(
                "Incorrect arguments. Use `on` or `off`.", mention_author=False
            )
            return

    @Cog.listener()
    async def on_member_join(self, member):
        ts = datetime.datetime.now(datetime.timezone.utc)
        cutoff_ts = ts - datetime.timedelta(hours=24)
        if member.created_at >= cutoff_ts or member.guild.id in self.raidmode:
            escaped_name = self.bot.escape_message(member)
            staff_channel = config.guild_configs[member.guild.id]["staff"][
                "staff_channel"
            ]
            embeds = []
            embed = discord.Embed(
                color=discord.Color.lighter_gray(),
                title="📥 User Joined",
                description=f"<@{member.id}> ({member.id})",
                timestamp=datetime.datetime.now(),
            )
            embed.set_footer(text="Dishwasher")
            embed.set_author(
                name=f"{escaped_name}", icon_url=f"{member.display_avatar.url}"
            )
            embed.set_thumbnail(url=f"{member.display_avatar.url}")
            embed.add_field(
                name="⏰ Account created:",
                value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
                inline=True,
            )
            embed.add_field(name="📨 Invite used:", value=f"{invite_used}", inline=True)
            if member.guild.id in self.raidmode:
                rmstr = "`🟢 ON`"
            else:
                rmstr = "`🔴 OFF`"
            embed.add_field(
                name="🚨 Raid mode...", value=f"is currently {rmstr}.", inline=False
            )
            embeds.append(embed)
            await member.guild.get_channel(staff_channel).send(embeds=embeds)


async def setup(bot):
    await bot.add_cog(ModObserve(bot))
