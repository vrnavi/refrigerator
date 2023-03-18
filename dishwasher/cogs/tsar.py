import config
import datetime
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff_or_ot


class journalBtn(discord.ui.View):
    @discord.ui.button(
        label="Get", custom_id="journalBtn", style=discord.ButtonStyle.primary
    )
    async def button_callback(self, interaction, button):
        role = interaction.guild.get_role(config.named_roles["journal"])
        if interaction.user.get_role(config.named_roles["journal"]) is not None:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                content="Removed your Journal role.", ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                content="Given your Journal role.", ephemeral=True
            )


class colorSel(discord.ui.View):
    def __init__(self):
        super().__init__()


class SAR(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.check(check_if_staff_or_ot)
    async def testcmd(self, ctx):
        """Temporarily creates a button."""
        options = []
        for r in config.color_roles:
            rr = self.bot.get_guild(config.guild_whitelist[0]).get_role(r)
            if rr.id == config.color_roles[0]:
                rn = "Fluctuating Phosphor"
                rc = "Changes each day!"
            else:
                rn = rr.name
                rc = "#%02x%02x%02x" % rr.color.to_rgb()
            options.append(discord.SelectOption(label=rn, value=rr.id, description=rc))
        select = discord.ui.Select(
            placeholder="Get a color!", options=options, min_values=1, max_values=1
        )

        async def select_callback(interaction):
            await interaction.response.send_message(f"Test. Picked {select.values[0]}.")

        select.callback = select_callback
        view = colorSel()
        view.add_item(select)
        await ctx.send(content="Test.", view=view)


async def setup(bot):
    await bot.add_cog(SAR(bot))
