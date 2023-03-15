import config
import datetime
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff_or_ot

class journalBtn(discord.ui.View):
    @discord.ui.button(label="Get", custom_id="journalBtn", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, button):
        role = interaction.guild.get_role(config.named_roles["journal"])
        if interaction.user.get_role(config.named_roles["journal"]) is not None:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(content="Removed your Journal role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(content="Given your Journal role.", ephemeral=True)            


    
class colorSel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # timeout of the view must be set to None

    @discord.ui.select(placeholder="Get a color!", min_values=1, max_values=1)
    async def select_callback(self, interaction, select):
        await interaction.response.send_message(f"Test. Picked {select.values[0]}.")

class SAR(Cog):            
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.check(check_if_staff_or_ot)
    async def testcmd(self, ctx):
        """Temporarily creates a button."""
        colorview = colorSel()
        for r in config.color_roles:
            rr = self.bot.get_guild(config.guild_whitelist[0]).get_role(r)
            rc = '#%02x%02x%02x' % rr.color.to_rgb()
            colorview.add_option(label=rr.name, value=rr.id, description=rc, default=False)
        await ctx.send(content="Test.", view=colorview)


async def setup(bot):
    await bot.add_cog(SAR(bot))
