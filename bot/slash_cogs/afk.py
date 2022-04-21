import asyncio
import discord
from discord.ext import commands
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot import db
from bot.db import models


class SlashAFK(commands.Cog):
    """
    Manage your AFK status
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def process_afk(self, message: discord.Message):
        async def run_afk(session: AsyncSession, member: discord.Member):
            q = select(models.AFK).where(models.AFK.user_id == member.id)
            result = await session.execute(q)

            if afk_data := result.scalar():
                await message.channel.send(
                    f"{member} is currently AFK because:\n*{afk_data.message}*",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

        async with db.async_session() as session:
            afk_tasks = [
                run_afk(session, member) for member in message.mentions
            ]
            await asyncio.gather(*afk_tasks)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            await self.process_afk(message)


def setup(bot):
    bot.add_cog(SlashAFK(bot))
