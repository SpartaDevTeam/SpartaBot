import re
import discord
from datetime import datetime
from discord.ext import commands
from discord.utils import _URL_REGEX

from bot import TESTING_GUILDS, THEME, db
from bot.db import models
from bot.enums import AutoModFeatures
from bot.views import AutoModView


class SlashAutoMod(commands.Cog):
    """
    Commands to setup Auto-Mod in Sparta
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def automod(self, ctx: discord.ApplicationContext):
        """
        Allows you to enable/disable automod features
        """

        async with db.async_session() as session:
            auto_mod_data = await session.get(models.AutoMod, ctx.guild.id)

            if not auto_mod_data:
                auto_mod_data = models.AutoMod(guild_id=ctx.guild.id)
                session.add(auto_mod_data)

            features = {
                attr: getattr(auto_mod_data, attr, False)
                for attr in dir(auto_mod_data)
                if not (
                    attr.startswith("_")
                    or attr.endswith("_")
                    or attr in ["guild_id", "registry", "metadata"]
                )
            }

            mod_embed = discord.Embed(
                title="Auto Mod",
                description="Allow Sparta to administrate on its own",
                color=THEME,
            )

            for feature in AutoModFeatures:
                if feature.name.lower() in features:
                    mod_embed.add_field(
                        name=feature.name.replace("_", " ").title(),
                        value=feature.value,
                        inline=False,
                    )

            mod_embed.set_footer(text="Enable or disable an Auto Mod feature")

            automod_view = AutoModView(features, ctx.author.id)
            await ctx.respond(embed=mod_embed, view=automod_view)
            await automod_view.wait()

            for feature, value in list(automod_view.features.items()):
                setattr(auto_mod_data, feature, value)

            await session.commit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        def ping_spam_check(msg: discord.Message) -> bool:
            return (
                (msg.author == message.author)
                and msg.mentions
                and message.mentions
                and (
                    datetime.utcnow().replace(tzinfo=msg.created_at.tzinfo)
                    - msg.created_at
                ).seconds
                < 5
            )

        async with db.async_session() as session:
            if data := await session.get(models.AutoMod, message.guild.id):
                auto_mod: models.AutoMod = data
            else:
                return

        if auto_mod.links:
            if re.search(_URL_REGEX, message.content):
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, You cannot send links "
                    "in this channel!",
                    delete_after=3,
                )

        if auto_mod.images:
            if any([hasattr(a, "width") for a in message.attachments]):
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, You cannot send images "
                    "in this channel!",
                    delete_after=3,
                )

        if auto_mod.ping_spam:
            if any(filter(ping_spam_check, self.bot.cached_messages)):
                await message.channel.send(
                    f"{message.author.mention}, Do not spam mentions "
                    "in this channel!",
                    delete_after=3,
                )


def setup(bot):
    bot.add_cog(SlashAutoMod(bot))
