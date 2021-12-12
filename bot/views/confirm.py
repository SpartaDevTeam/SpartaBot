import discord
from discord import ButtonStyle


class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.do_action: bool

    @discord.ui.button(label="Confirm", style=ButtonStyle.danger)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.do_action = True
        self.stop()
        await interaction.message.delete()

    @discord.ui.button(label="Cancel", style=ButtonStyle.grey)
    async def cancel(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.do_action = False
        self.stop()
        await interaction.message.delete()
