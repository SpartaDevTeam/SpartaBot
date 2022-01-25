import asyncio
import youtube_dl
import discord
from discord.ext import commands

from bot import TESTING_GUILDS, THEME
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

    queues: dict[int, list[YTDLSource]] = {}
    current_players: dict[int, YTDLSource] = {}
    play_next: dict[int, bool] = {}

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def music_queue(self, guild: discord.Guild):
        guild_queue: list[YTDLSource] = self.queues[guild.id]
        voice_client: discord.VoiceClient = guild.voice_client
        self.play_next[guild.id] = False

        def after_callback(error):
            if error:
                print(f"Player error: {error}")

            self.play_next[guild.id] = True
            print("Finished playing a song")

        while guild_queue:
            player = guild_queue.pop(0)
            self.current_players[guild.id] = player

            self.play_next[guild.id] = False
            voice_client.play(
                player,
                after=after_callback,
            )

            while not self.play_next[guild.id]:
                await asyncio.sleep(1)

            guild_queue = self.queues[guild.id]

        del self.queues[guild.id]
        del self.current_players[guild.id]
        del self.play_next[guild.id]

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def play(self, ctx: discord.ApplicationContext, song_name: str):
        """
        Add a song to the queue
        """

        video_url = await search_youtube(song_name)
        player = await YTDLSource.from_url(
            video_url, loop=ctx.bot.loop, stream=True
        )

        if ctx.guild_id not in self.queues:
            self.queues[ctx.guild_id] = []
            asyncio.create_task(self.music_queue(ctx.guild))

        self.queues[ctx.guild_id].append(player)
        await ctx.respond(f"Added to queue: `{player.title}`")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def queue(self, ctx: discord.ApplicationContext):
        """
        View all the songs currently in the queue
        """

        guild_queue = self.queues[ctx.guild_id]
        current_player = self.current_players[ctx.guild_id]
        queue_embed = discord.Embed(title="Song Queue", color=THEME)

        # Current player
        channel = current_player.data["channel"]
        duration_mins = str(current_player.data["duration"] // 60)
        duration_secs = str(current_player.data["duration"] % 60).zfill(2)
        queue_embed.add_field(
            name=f"Currently Playing - {current_player.title}",
            value=f"**Duration:** {duration_mins}:{duration_secs}\n**By:** {channel}",
            inline=False,
        )

        for player in guild_queue:
            channel = player.data["channel"]
            duration_mins = str(player.data["duration"] // 60)
            duration_secs = str(player.data["duration"] % 60).zfill(2)
            queue_embed.add_field(
                name=player.title,
                value=f"**Duration:** {duration_mins}:{duration_secs}\n**By:** {channel}",
                inline=False,
            )

        await ctx.respond(embed=queue_embed)

    @play.before_invoke
    async def ensure_voice(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        if author_vc := ctx.author.voice:
            if existing_vc := ctx.guild.voice_client:
                if existing_vc.channel.id != author_vc.channel.id:
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
    bot.add_cog(SlashMusic(bot))
