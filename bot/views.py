import asyncio
from math import ceil
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
    def __init__(
        self, label: str, feature_name: str, enabled: bool, author_id: int
    ):
        self.feature_name = feature_name
        self.author_id = author_id
        self.enabled = enabled

        if enabled:
            style = ButtonStyle.success
        else:
            style = ButtonStyle.danger

        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            return

        self.enabled = not self.enabled

        if self.enabled:
            self.style = ButtonStyle.success
        else:
            self.style = ButtonStyle.danger

        self.view.set_feature(self.feature_name, self.enabled)
        await interaction.message.edit(view=self.view)


class AutoModView(discord.ui.View):
    def __init__(self, feature_options: dict[str, bool], author_id: int):
        self.author_id = author_id
        self.features = feature_options
        children = []

        for feature, enabled in list(feature_options.items()):
            button = AutoModButton(
                feature.replace("_", " ").title(), feature, enabled, author_id
            )
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


class PollButton(discord.ui.Button):
    def __init__(self, number: int):
        self.number = number
        super().__init__(label=str(number), style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if view := self.view:
            await view.user_vote(interaction, self.number)


class PollView(discord.ui.View):
    def __init__(self, options: list[str], poll_length: float):
        self.options = options

        self.votes: dict[str, int] = {}  # key: option, value: numbers of votes
        self.voters: list[int] = []  # list of user ids

        children = []
        for number, option_name in enumerate(options, start=1):
            self.votes[option_name] = 0
            button = PollButton(number)
            children.append(button)

        length_seconds = int(poll_length * 60)
        super().__init__(*children, timeout=None)
        asyncio.create_task(self.stop_poll(length_seconds))

    async def stop_poll(self, time: int):
        await asyncio.sleep(time)
        self.stop()

    async def user_vote(self, interaction: discord.Interaction, number: int):
        if not interaction.user:
            return

        if interaction.user.id not in self.voters:
            option_name = self.options[number - 1]
            self.votes[option_name] += 1

            self.voters.append(interaction.user.id)
            await interaction.response.send_message(
                f"You voted for **{option_name}**", ephemeral=True
            )

        else:
            await interaction.response.send_message(
                "You cannot vote in the same poll twice!", ephemeral=True
            )


class SuggestView(discord.ui.View):
    anonymous: bool

    def __init__(self, author_id: int):
        super().__init__(timeout=5)
        self.author_id = author_id

    @discord.ui.button(label="Yes", style=ButtonStyle.primary)
    async def yes(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.author_id == interaction.user.id:
            self.anonymous = False
            self.stop()
            await interaction.message.edit(content="Sending...", view=None)

    @discord.ui.button(label="No", style=ButtonStyle.secondary)
    async def no(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.author_id == interaction.user.id:
            self.anonymous = True
            self.stop()
            await interaction.message.edit(content="Sending...", view=None)


class PaginatedSelectView(discord.ui.View):
    """
    Paginated select menu for more than 25 options.

    Args:
        author_id (int): ID of the user who issued the command which instances this view
        options (list): List of selectable options.
        values (list): List of values corresponding to the options.
        descriptions (list, optional): List of descriptions corresponding to the options. Defaults to [].
        emojis (list, optional): List of emojis corresponding to the options. Defaults to [].
        max_values (int, optional): Maximum options that can be selected. Defaults to 1.
    """

    selected_values = []
    current_page = 0

    def __init__(
        self,
        author_id: int,
        options: list,
        values: list,
        descriptions: list = [],
        emojis: list = [],
        max_values: int = 1,
    ):
        self.author_id = author_id
        self.options = options
        self.values = values
        self.descriptions = descriptions
        self.emojis = emojis
        self.max_values = max_values

        items = self.build_view()
        super().__init__(*items)

    def build_view(self) -> list[discord.ui.Item]:
        items = []

        limits = (self.current_page * 25, (self.current_page + 1) * 25)
        options = self.options[limits[0] : limits[1]]
        values = self.values[limits[0] : limits[1]]
        descriptions = self.descriptions[limits[0] : limits[1]]
        emojis = self.emojis[limits[0] : limits[1]]
        zipped_options = zip(options, values, descriptions, emojis)

        max_pages = ceil(len(self.options) / 25)
        select_menu = discord.ui.Select(
            placeholder=f"Page {self.current_page + 1} of {max_pages}",
            max_values=min(len(options), self.max_values),
            row=0,
        )
        select_menu.callback = self.select_menu_callback

        for option, value, description, emoji in zipped_options:
            select_menu.add_option(
                label=option, value=value, description=description, emoji=emoji
            )

        items.append(select_menu)

        if len(self.options) > 25:
            prev_button = discord.ui.Button(emoji="⏪", row=1)
            prev_button.callback = self.previous_page
            prev_button.disabled = self.current_page <= 0
            items.append(prev_button)

            next_button = discord.ui.Button(emoji="⏩", row=1)
            next_button.callback = self.next_page
            next_button.disabled = (
                self.current_page + 1 >= len(self.options) / 25
            )
            items.append(next_button)

        delete_button = discord.ui.Button(
            label="Delete", style=ButtonStyle.danger, row=2
        )
        delete_button.callback = self.delete
        items.append(delete_button)

        return items

    async def next_page(self, interaction: discord.Interaction):
        if (
            interaction.user.id == self.author_id
            and self.current_page + 1 < len(self.options) / 25
        ):
            self.current_page += 1
            self.clear_items()

            for item in self.build_view():
                self.add_item(item)

            await interaction.message.edit(view=self)

    async def previous_page(self, interaction: discord.Interaction):
        if interaction.user.id == self.author_id and self.current_page > 0:
            self.current_page -= 1
            self.clear_items()

            for item in self.build_view():
                self.add_item(item)

            await interaction.message.edit(view=self)

    async def select_menu_callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            self.selected_values = interaction.data["values"]

    async def delete(self, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            self.stop()


class PaginatedEmbedView(discord.ui.View):
    current_embed_index = 0

    def __init__(self, author_id: int, embeds: list[discord.Embed]):
        super().__init__()
        self.author_id = author_id
        self.embeds = embeds

    @discord.ui.button(emoji="⏪")
    async def previous(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if not interaction.user.id == self.author_id:
            return

        self.current_embed_index -= 1

        if self.current_embed_index < 0:
            self.current_embed_index = len(self.embeds) - 1

        embed = self.embeds[self.current_embed_index]
        await interaction.message.edit(embed=embed)

    @discord.ui.button(emoji="⏩")
    async def next(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if not interaction.user.id == self.author_id:
            return

        self.current_embed_index += 1

        if self.current_embed_index >= len(self.embeds):
            self.current_embed_index = 0

        embed = self.embeds[self.current_embed_index]
        await interaction.message.edit(embed=embed)

    @discord.ui.button(emoji="❌")
    async def close(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if interaction.id == self.author_id:
            await interaction.message.delete()
            self.stop()
