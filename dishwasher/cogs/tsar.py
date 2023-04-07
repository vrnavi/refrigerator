import config
import datetime
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff_or_ot, check_if_bot_manager


class tsarList:
    def __init__(self):
        self.openmessages = {}
        self.tocembed = discord.Embed(
            title="Table of Contents",
            description="*Use the buttons below to turn the page.*",
            color=discord.Color.from_str("#9cd8df"),
            timestamp=datetime.datetime.now(),
        )
        self.tocembed.set_image(
            url="https://cdn.discordapp.com/attachments/263715783782301696/1093726711553724546/sol_journal_glow2.png"
        )
        self.tocembed.set_author(
            name="The OneShot Discord and You",
            icon_url="https://cdn.discordapp.com/attachments/263715783782301696/1093731958074392616/item_blue_journal_glow.png",
        )
        self.tocembed.add_field(
            name="Section 1",
            value="🔨 Moderation",
            inline=True,
        )
        self.tocembed.add_field(
            name="Section 2",
            value="📂 Channels",
            inline=True,
        )
        self.tocembed.add_field(
            name="Section 3",
            value="🌈 Roles",
            inline=True,
        )
        self.tocembed.add_field(
            name="Section 4",
            value="🛠️ Bots",
            inline=True,
        )
        self.tocembed.add_field(
            name="Section 5",
            value="🗃️ Links",
            inline=True,
        )
        self.tocembed.add_field(
            name="Section 6",
            value="📜 FAQ",
            inline=True,
        )
        self.bot = None

    def set(self, user, message):
        self.openmessages[user] = message
        
    def setbot(self, bot):
        self.bot = bot

    def get(self, user):
        return self.openmessages[user]

    def toc(self):
        self.tocembed.set_footer(
            text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar
        )
        return self.tocembed


class journalBtn(discord.ui.View):
    @discord.ui.button(
        label="Get", custom_id="journalBtn", style=discord.ButtonStyle.primary
    )
    async def button_callback(self, interaction, button):
        role = interaction.guild.get_role(config.named_roles["journal"])
        age = interaction.user.joined_at - interaction.user.created_at
        if age < datetime.timedelta(hours=24):
            await interaction.response.send_message(
                content="Your account is too new to get this.", ephemeral=True
            )
            return
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


class tocBtns(discord.ui.View):
    @discord.ui.button(
        label="Moderation",
        style=discord.ButtonStyle.primary,
        emoji="🔨",
    )
    async def moderationbutton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        msg = tsarList.get(interaction.user)

    @discord.ui.button(
        label="Channels",
        style=discord.ButtonStyle.primary,
        emoji="📂",
    )
    async def channelbutton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        msg = tsarList.get(interaction.user)

    @discord.ui.button(
        label="Roles",
        style=discord.ButtonStyle.primary,
        emoji="🌈",
    )
    async def rolesbutton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        msg = tsarList.get(interaction.user)

    @discord.ui.button(
        label="Bots",
        style=discord.ButtonStyle.primary,
        emoji="🛠️",
    )
    async def botsbutton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        msg = tsarList.get(interaction.user)

    @discord.ui.button(
        label="Links",
        style=discord.ButtonStyle.primary,
        emoji="🗃️",
    )
    async def linksbutton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        msg = tsarList.get(interaction.user)

    @discord.ui.button(
        label="FAQ",
        style=discord.ButtonStyle.primary,
        emoji="📜",
    )
    async def faqbutton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        msg = tsarList.get(interaction.user)


class ctrlsBtn(discord.ui.View):
    @discord.ui.button(
        label="Open Index",
        custom_id="ctrlsBtn",
        style=discord.ButtonStyle.primary,
        emoji="📖",
    )
    async def button_callback(self, interaction, button):
        embed = tsarList.toc()
        view = tocBtns()
        msg = await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        tsarList.set(interaction.user, msg)


class TSAR(Cog):
    """
    True Self Assignable Roles. Or in other words, the OSD's Rules and Information channels.
    """

    def __init__(self, bot):
        self.bot = bot
        tsarList.setbot(bot)

    @commands.guild_only()
    @commands.command()
    @commands.check(check_if_bot_manager)
    async def colorget(self, ctx):
        """Creates a droptown to get color roles.."""
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

    @commands.guild_only()
    @commands.command()
    @commands.check(check_if_bot_manager)
    async def infosetup(self, ctx):
        embed = discord.Embed(
            title="The OneShot Discord and You",
            description="Enclosed below is a guide to the OneShot Discord.\nPlease click the 📖 **Open Index** button to get started.\nYou can also view it in website form via the link above.",
            color=discord.Color.from_str("#9cd8df"),
            timestamp=datetime.datetime.now(),
            url="https://oneshot.whistler.page",
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/263715783782301696/1093726711323049994/sol_journal_glow1.png"
        )
        embed.set_author(
            name="renavi's", url="https://0ccu.lt", icon_url="https://0ccu.lt/sigil.png"
        )
        embed.set_footer(text="Dishwasher", icon_url=self.bot.user.display_avatar)
        view = ctrlsBtn()
        await ctx.send(
            content="If you are unable to see the embed below:\n🔹 `Settings`\n🔹 `Text & Images`\n🔹 `Show embeds and preview website links pasted into chat`",
            embed=embed,
            view=view,
        )
        await ctx.message.delete()


tsarList = tsarList()


async def setup(bot):
    await bot.add_cog(TSAR(bot))
