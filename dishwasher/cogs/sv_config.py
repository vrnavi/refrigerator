import json
import discord
import datetime
import config
from helpers.checks import check_if_staff, check_if_bot_manager
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.sv_config import (
    fill_config,
    make_config,
    set_config,
    stock_configs,
    friendly_names,
)


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
                f = f"**{friendly_names[k]}**" + "\n" if k in friendly_names else ""
                if not v and str(v) != "False":
                    v = f"Not Configured ({type(v).__name__})"
                if str(v) == "None":
                    v = "Forcibly Disabled"
                lines += f"\n{f}`{k}`\n{v}"
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
        await ctx.reply(
            content=f"The configuration for **{guild}** has been reset.",
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @configs.command()
    async def set(self, ctx, category, setting, *, value=None):
        """[S] Sets the configuration for a guild."""
        configs = fill_config(ctx.guild.id)
        category = category.lower()
        setting = setting.lower()
        if category not in configs or setting not in configs[category]:
            if category not in stock_configs or setting not in stock_configs[category]:
                return await ctx.reply(
                    content="You specified an invalid category or setting.",
                    mention_author=False,
                )
            else:
                configs = set_config(
                    ctx.guild.id, category, setting, stock_configs[category][setting]
                )
        if configs[category][setting] == None:
            return await ctx.reply(
                content="This setting has been administratively disabled by the bot owner.",
                mention_author=True,
            )
        settingtype = type(configs[category][setting]).__name__
        if settingtype == "str":
            if not value:
                value = ""
            set_config(ctx.guild.id, category, setting, value)
            return await ctx.reply(
                content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{value}`.",
                mention_author=False,
            )
        elif settingtype == "int":
            if not value:
                value = 0
            try:
                set_config(ctx.guild.id, category, setting, int(value))
                return await ctx.reply(
                    content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{value}`.",
                    mention_author=False,
                )
            except ValueError:
                return await ctx.reply(
                    content="This setting requires an `int` to be given.\nYou can supply numbers only.",
                    mention_author=False,
                )
        elif settingtype == "list":
            pre_cfg = configs[category][setting]
            if value:
                if value.split()[0] == "add":
                    set_config(
                        ctx.guild.id, category, setting, pre_cfg + value.split()[1:]
                    )
                    return await ctx.reply(
                        content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{pre_cfg + value.split()[1:]}`.",
                        mention_author=False,
                    )
                elif value.split()[0] == "remove":
                    if not pre_cfg:
                        return await ctx.reply(
                            content="There is nothing to remove.", mention_author=False
                        )
                    for v in value.split()[1:]:
                        if v not in pre_cfg:
                            await ctx.reply(
                                content=f"{v} is not present in this setting, skipping.",
                                mention_author=False,
                            )
                            continue
                        pre_cfg.remove(v)
                        set_config(ctx.guild.id, category, setting, pre_cfg)
                    return await ctx.reply(
                        content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{pre_cfg}`.",
                        mention_author=False,
                    )
                else:
                    set_config(ctx.guild.id, category, setting, value.split())
                    return await ctx.reply(
                        content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{value.split()}`.",
                        mention_author=False,
                    )
            else:
                set_config(ctx.guild.id, category, setting, [])
                return await ctx.reply(
                    content=f"**{category.title()}/**`{setting}` has been updated with a new value of `[]`.",
                    mention_author=False,
                )
        elif settingtype == "bool":
            if value.title() not in ("True", "False"):
                return await ctx.reply(
                    content="This setting requires a `bool` to be given.\nYou can supply `true` or `false`.",
                    mention_author=False,
                )
            if setting == "enable":
                for k, v in configs[category].items():
                    if not v:
                        return await ctx.reply(
                            content="This feature cannot be enabled unless the other settings in the category are properly configured.\nPlease configure these settings first, then try again.",
                            mention_author=False,
                        )
            set_config(
                ctx.guild.id,
                category,
                setting,
                True if value.title() == "True" else False,
            )
            return await ctx.reply(
                content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{value}`.",
                mention_author=False,
            )


async def setup(bot: Bot):
    await bot.add_cog(sv_config(bot))
