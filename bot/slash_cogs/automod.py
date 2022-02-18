import json
import re
import discord
from datetime import datetime
from discord.ext import commands
from discord.utils import _URL_REGEX

from bot import TESTING_GUILDS, THEME
from bot.data import Data
from bot.enums import AutoModFeatures
from bot.views import AutoModView


class SlashAutoMod(commands.Cog):
    """
    Commands to setup Auto-Mod in Sparta
    """

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def automod(self, ctx: discord.ApplicationContext):
        """
        Allows you to enable/disable automod features
        """

        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "SELECT activated_automod FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        activated_features = json.loads(Data.c.fetchone()[0])

        def save():
            Data.c.execute(
                "UPDATE guilds SET activated_automod = :new_features WHERE id = :guild_id",
                {
                    "new_features": json.dumps(activated_features),
                    "guild_id": ctx.guild.id,
                },
            )
            Data.conn.commit()

        mod_embed = discord.Embed(
            title="Auto Mod",
            description="Allow Sparta to administrate on its own",
            color=THEME,
        )
        view_data = {}

        for feature in AutoModFeatures:
            lower_name = feature.name.lower()
            view_data[lower_name] = lower_name in activated_features

            mod_embed.add_field(
                name=feature.name.capitalize(),
                value=feature.value,
                inline=False,
            )

        mod_embed.set_footer(text="Enable or disable an Auto Mod feature")

        automod_view = AutoModView(view_data, ctx.author.id)
        await ctx.respond(embed=mod_embed, view=automod_view)
        await automod_view.wait()

        new_features = list(automod_view.features.items())
        activated_features = [
            feature for feature, enabled in new_features if enabled
        ]
        save()

    # TODO: Enable when removing prefix commands
    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if not message.guild or message.author.bot:
    #         return

    #     def spam_check(msg):
    #         return (
    #             (msg.author == message.author)
    #             and len(msg.mentions)
    #             and (
    #                 (
    #                     datetime.datetime.utcnow().replace(
    #                         tzinfo=msg.created_at.tzinfo
    #                     )
    #                     - msg.created_at
    #                 ).seconds
    #                 < 20
    #             )
    #         )

    #     Data.check_guild_entry(message.guild)

    #     Data.c.execute(
    #         "SELECT activated_automod FROM guilds WHERE id = :guild_id",
    #         {"guild_id": message.guild.id},
    #     )
    #     activated_features = json.loads(Data.c.fetchone()[0])

    #     # if channel id's data contains "links":
    #     if "links" in activated_features:
    #         if search(self.url_regex, message.content):
    #             await message.delete()
    #             await message.channel.send(
    #                 f"{message.author.mention}, You cannot send links "
    #                 "in this channel!",
    #                 delete_after=3,
    #             )

    #     # if channel id's data contains "images"
    #     if "images" in activated_features:
    #         if any([hasattr(a, "width") for a in message.attachments]):
    #             await message.delete()
    #             await message.channel.send(
    #                 f"{message.author.mention}, You cannot send images "
    #                 "in this channel!",
    #                 delete_after=3,
    #             )

    #     # if channel id's data contains "spam":
    #     if "spam" in activated_features:
    #         if (
    #             len(
    #                 list(
    #                     filter(
    #                         lambda m: spam_check(m), self.bot.cached_messages
    #                     )
    #                 )
    #             )
    #             >= 5
    #         ):
    #             await message.channel.send(
    #                 f"{message.author.mention}, Do not spam mentions "
    #                 "in this channel!",
    #                 delete_after=3,
    #             )


def setup(bot):
    bot.add_cog(SlashAutoMod())
