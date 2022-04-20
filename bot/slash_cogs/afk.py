import asyncio
import discord
from discord.ext import commands
from sqlalchemy.future import select

from bot import db
from bot.db import models


class SlashAFK(commands.Cog):
    """
    Manage your AFK status
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def process_afk(self, message: discord.Message):
        async def run_afk(afk_data: models.AFK):
            user = await self.bot.fetch_user(afk_data.user_id)
            if user in message.mentions:
                await message.channel.send(
                    f"{user} is currently AFK because:\n*{afk_data.message}*",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

        async with db.async_session() as session:
            q = select(models.AFK)
            result = await session.execute(q)
            afk_tasks = [run_afk(afk) for afk in result.scalars()]

        await asyncio.gather(*afk_tasks)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            await self.process_afk(message)


def setup(bot):
    bot.add_cog(SlashAFK(bot))
