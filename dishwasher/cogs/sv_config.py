import json
import discord
import datetime
import config
from helpers.checks import check_if_staff, check_if_bot_manager
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.sv_config import fill_config, make_config, set_config, friendly_names


class sv_config(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(invoke_without_command=True)
    async def configs(self, ctx, guild: discord.Guild = None):
        """[S] Gets the configuration for a guild."""
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
                if str(v) == "None":
                    v = "Forcibly Disabled"
                lines += f"\n**{k}**\n{v}"
            embed.add_field(
                name=p.title(),
                value=lines,
                inline=True,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def reset(self, ctx, guild: discord.Guild = None):
        """[S] Resets the configuration for a guild."""
        if not guild:
            guild = ctx.guild
        make_configs(guild.id)
        await ctx.reply(content=f"The configuration for **{guild}** has been reset.", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @configs.command()
    async def set(self, ctx, category, setting, *, value):
        """[S] Sets the configuration for a guild."""
        configs = fill_config(ctx.guild.id)
        category = category.lower()
        setting = setting.lower()
        if category not in configs or setting not in configs[category] and :
            return await ctx.reply(content="You specified an invalid category or setting.", mention_author=False)
        if type(configs[category][setting]).__name__ == "str":
            configs[category][setting] = value
        
        
        await ctx.reply(content=f"The configuration for **{guild}** has been reset.", mention_author=False)
        
        
        


async def setup(bot: Bot):
    await bot.add_cog(sv_config(bot))
