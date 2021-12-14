import discord
from discord import ButtonStyle


class ConfirmView(discord.ui.View):
    do_action: bool

    def __init__(self, author_id: int):
        super().__init__()
        self.author_id = author_id

    @discord.ui.button(label="Confirm", style=ButtonStyle.danger)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.author_id == interaction.user.id:
            self.do_action = True
            self.stop()
            await interaction.message.edit(content="Confirming...", view=None)

    @discord.ui.button(label="Cancel", style=ButtonStyle.grey)
    async def cancel(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.author_id == interaction.user.id:
            self.do_action = False
            self.stop()
            await interaction.message.edit(content="Cancelling...", view=None)


class AutoModButton(discord.ui.Button):
    def __init__(self, label: str, enabled: bool, author_id: int):
        self.author_id = author_id

        if enabled:
            style = ButtonStyle.success
        else:
            style = ButtonStyle.danger

        self.enabled = enabled
        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            return

        self.enabled = not self.enabled

        if self.enabled:
            self.style = ButtonStyle.success
        else:
            self.style = ButtonStyle.danger

        self.view.set_feature(self.label.lower(), self.enabled)
        await interaction.message.edit(view=self.view)


class AutoModView(discord.ui.View):
    def __init__(self, feature_options: dict[str, bool], author_id: int):
        self.author_id = author_id
        self.features = feature_options
        children = []

        for feature, enabled in list(feature_options.items()):
            button = AutoModButton(feature.capitalize(), enabled, author_id)
            children.append(button)

        super().__init__(*children)

    def set_feature(self, feature: str, value: bool):
        self.features[feature] = value

    @discord.ui.button(label="Save", style=ButtonStyle.secondary)
    async def save(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.author_id == interaction.user.id:
            self.stop()
            await interaction.message.edit(
                content="Options have been saved", view=None, embed=None
            )
