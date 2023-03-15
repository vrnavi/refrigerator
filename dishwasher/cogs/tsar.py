import config
import datetime
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff_or_ot

class journalBtn(discord.ui.View):
    @discord.ui.button(label="Get", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, button):
        role = interaction.guild.get_role(config.named_roles["journal"])
        if interaction.user.get_role(config.named_roles["journal"]) is not None:
            await interaction.user.remove_role(role)
            await interaction.response.send_message(content="Removed your Journal role.", ephemeral=True, delete_after=5)
        else:
            await interaction.user.add_role(config.named_roles["journal"])
            await interaction.response.send_message(content="Given your Journal role.", ephemeral=True, delete_after=5)
            

class SAR(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.check(check_if_staff_or_ot)
    async def testcmd(self, ctx):
        """Temporarily creates a button."""
        await ctx.send(content="Test.", view=journalBtn())


async def setup(bot):
    await bot.add_cog(SAR(bot))
