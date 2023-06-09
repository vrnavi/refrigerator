import json
import discord
import datetime
import config
from helpers.checks import check_if_staff, check_if_bot_manager
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.sv_config import fill_config, friendly_names


class sv_config(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(invoke_without_command=True)
    async def configs(self, ctx, guild: discord.Guild = None):
        """[O] Gets the configuration for a guild."""
        if not guild:
            guild = ctx.guild
        configs = fill_config(guild.id)
        embed = discord.Embed(
            title=f"⚙️ Configuration for {guild}",
            description=f"Tweak a setting with `{config.prefixes[0]}configs set <category> <setting> <value>`.",
            color=ctx.author.color,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        for p, s in configs.items():
            lines = ""
            for k, v in s.items():
                if k in friendly_names:
                    k = friendly_names[k]
                if not v and str(v) != "False":
                    v = f"Not Configured ({type(v).__name__})"
                lines += f"\n**{k}**\n{v}"
            embed.add_field(
                name=p.title(),
                value=lines,
                inline=True,
            )
        await ctx.reply(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(sv_config(bot))
