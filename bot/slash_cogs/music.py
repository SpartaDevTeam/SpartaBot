import asyncio
import youtube_dl
import discord
from discord.ext import commands

from bot import TESTING_GUILDS
from bot.utils import search_youtube

youtube_dl.utils.bug_reports_message = lambda: ""


class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_format_options = {
        "format": "bestaudio/best",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
    }
    ffmpeg_options = {"options": "-vn"}

    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: cls.ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else cls.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(filename, **cls.ffmpeg_options), data=data
        )


class SlashMusic(commands.Cog):
    """
    Jam to your favorite tunes with your favorite bot
    """

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def play(self, ctx: discord.ApplicationContext, song_name: str):
        """
        Streams a song from YouTube
        """

        video_url = await search_youtube(song_name)
        player = await YTDLSource.from_url(
            video_url, loop=ctx.bot.loop, stream=True
        )
        ctx.guild.voice_client.play(
            player,
            after=lambda e: print(f"Player error: {e}") if e else None,
        )

        await ctx.respond(f"Now playing: {player.title}")

    @play.before_invoke
    async def ensure_voice(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        if author_vc := ctx.author.voice:
            if existing_vc := ctx.guild.voice_client:
                if existing_vc.channel.id == author_vc.channel.id:
                    existing_vc.stop()
                else:
                    await ctx.respond(
                        f"I'm already in {existing_vc.channel.mention}, please join that channel."
                    )
                    raise discord.ApplicationCommandError(
                        "Author not connected to bot's voice channel."
                    )

            else:
                await author_vc.channel.connect()

        else:
            await ctx.respond(
                "Please connect to a voice channel before using this command"
            )
            raise discord.ApplicationCommandError(
                "Author not connected to a voice channel."
            )


def setup(bot):
    bot.add_cog(SlashMusic())
