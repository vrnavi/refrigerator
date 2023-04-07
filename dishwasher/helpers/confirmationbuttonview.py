from typing import Optional, Callable
from discord import Interaction
from discord.ui import View, Button, button

class ConfirmationButtonView(View):
    def __init__(self, *, timeout: Optional[float] = 180, author_id: int, yes_action: Callable, no_action: Callable):
        super().__init__(timeout=timeout)
        self.yes_action = yes_action
        self.no_action = no_action
        self.author_id = author_id

    @button(label="Yes", custom_id="button_yes")
    async def button_yes(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        await interaction.message.delete()
        await self.yes_action()
        self.stop()

    @button(label="No", custom_id="button_no")
    async def button_no(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        await interaction.message.delete()
        await self.no_action()
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        return self.author_id == interaction.user.id
