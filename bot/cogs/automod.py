import discord
from discord.ext import commands

from bot import MyBot, db
from bot.db import models


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.description = "Commands to setup Auto-Mod in Sparta"
        self.theme_color = discord.Color.purple()

    @commands.command(
        name="automod", help="Allows you to enable/disable automod features"
    )
    @commands.has_guild_permissions(administrator=True)
    async def automod(self, ctx: commands.Context):
        def check(message: discord.Message):
            return (
                message.channel == ctx.channel
                and message.author == ctx.message.author
            )

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

            async def save():
                for feature, value in list(features.items()):
                    setattr(auto_mod_data, feature, value)

                await session.commit()

            mod_embed = discord.Embed(
                title="Auto Mod",
                description=(
                    "Allow Sparta to administrate on its own. "
                    "Reply with a particular feature."
                ),
                color=self.theme_color,
            )
            mod_embed.set_footer(
                text=(
                    "Reply with stop if you want to stop "
                    "adding auto-mod features and save your changes"
                )
            )
            mod_embed.add_field(
                name="Options",
                value="\n".join(
                    [f"{i + 1}) `{f}`" for i, f in enumerate(features)]
                ),
            )

            await ctx.send(embed=mod_embed)

            while True:
                msg = await self.bot.wait_for("message", check=check)
                msg = str(msg.content).lower()

                if msg in features:
                    if features[msg]:
                        await ctx.send(f"Removed `{msg}`!")
                        features[msg] = False
                    else:
                        await ctx.send(f"Added `{msg}`!")
                        features[msg] = True

                elif msg == "stop":
                    await save()
                    await ctx.send("The changes have been saved!")
                    break


def setup(bot):
    bot.add_cog(AutoMod(bot))
