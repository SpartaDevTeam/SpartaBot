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

    # TODO: Add remove from queue, loop command

    queues: dict[int, list[YTDLSource]] = {}
    current_players: dict[int, YTDLSource] = {}
    play_next: dict[int, bool] = {}
    skip_song: dict[int, bool] = {}

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def music_queue(self, ctx: discord.ApplicationContext):
        voice_client: discord.VoiceClient = ctx.guild.voice_client

        song_queue: list[YTDLSource] = self.queues[ctx.guild_id]
        self.play_next[ctx.guild_id] = False
        self.skip_song[ctx.guild_id] = False

        def after_callback(error):
            if error:
                print(f"Player error: {error}")
                asyncio.create_task(
                    ctx.send("An error occurred while playing the song.")
                )

            self.play_next[ctx.guild_id] = True
            print("Finished playing a song")

        while song_queue:
            player = song_queue.pop(0)
            self.current_players[ctx.guild_id] = player

            await ctx.send(f"Now playing: `{player.title}`")

            self.play_next[ctx.guild_id] = False
            voice_client.play(
                player,
                after=after_callback,
            )

            while (
                not self.play_next[ctx.guild_id]
                and not self.skip_song[ctx.guild_id]
            ):
                await asyncio.sleep(1)

            # Update local queue
            voice_client.stop()
            self.skip_song[ctx.guild_id] = False
            song_queue = self.queues[ctx.guild_id]

            # Check if vc is not empty
            ch: discord.VoiceChannel = await ctx.guild.fetch_channel(
                voice_client.channel.id
            )
            if len(ch.members) <= 1:
                break

        if song_queue:
            await ctx.send(
                "Leaving the voice channel because everybody left..."
            )
        else:
            await ctx.send(
                "Leaving the voice channel because the song queue is over..."
            )

        self.clear_guild_queue(ctx.guild_id)
        await voice_client.disconnect()

    def clear_guild_queue(self, guild_id: int):
        del self.queues[guild_id]
        del self.current_players[guild_id]
        del self.play_next[guild_id]
        del self.skip_song[guild_id]

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def play(self, ctx: discord.ApplicationContext, song_name: str):
        """
        Add a song to the queue
        """

        if not ctx.guild.voice_client:
            await ctx.author.voice.channel.connect()

        video_url = await search_youtube(song_name)
        player = await YTDLSource.from_url(
            video_url, loop=ctx.bot.loop, stream=True
        )

        if ctx.guild_id not in self.queues:
            self.queues[ctx.guild_id] = []
            asyncio.create_task(self.music_queue(ctx))

        self.queues[ctx.guild_id].append(player)
        await ctx.respond(f"Added to queue: `{player.title}`")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def leave(
        self, ctx: discord.ApplicationContext, clear_queue: bool = False
    ):
        """
        Leave the current voice channel
        """

        is_author_admin: discord.Permissions = (
            ctx.author.guild_permissions.administrator
            or ctx.author.id == ctx.guild.owner_id
        )

        if clear_queue and not is_author_admin:
            await ctx.respond(
                "You need `Administrator` permissions to clear the song queue",
                ephemeral=True,
            )
            return

        if bot_vc := ctx.guild.voice_client:
            if clear_queue:
                self.clear_guild_queue(ctx.guild_id)

            await bot_vc.disconnect()
            await ctx.respond("Left the voice channel")

        else:
            await ctx.respond(
                "I'm not connected to a voice channel", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def skip(self, ctx: discord.ApplicationContext):
        """
        Skip the current song
        """

        if not ctx.guild.voice_client:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

        self.skip_song[ctx.guild_id] = True
        await ctx.respond("Song has been skipped")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def resume(self, ctx: discord.ApplicationContext):
        """
        Resume the song that was playing
        """

        if bot_vc := ctx.guild.voice_client:
            if bot_vc.is_paused():
                bot_vc.resume()
                await ctx.respond("Resuming the song...")
            else:
                await ctx.respond("The song is already playing")

        else:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def pause(self, ctx: discord.ApplicationContext):
        """
        Pause the song that is playing
        """

        if bot_vc := ctx.guild.voice_client:
            if not bot_vc.is_paused():
                bot_vc.pause()
                await ctx.respond("Pausing the song...")
            else:
                await ctx.respond("The song is already paused")

        else:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def volume(self, ctx: discord.ApplicationContext, new_volume: int):
        """
        Change the volume of the song that is playing
        """

        if bot_vc := ctx.guild.voice_client:
            new_volume = max(0, min(new_volume, 100))
            bot_vc.source.volume = new_volume / 100
            await ctx.respond(f"Volume changed to **{new_volume}%**")
        else:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def queue(self, ctx: discord.ApplicationContext):
        """
        View all the songs currently in the queue
        """

        guild_queue = self.queues.get(ctx.guild_id)
        current_player = self.current_players.get(ctx.guild_id)

        if not (bot_vc := ctx.guild.voice_client):
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )
            return

        queue_embed = discord.Embed(title="Song Queue", color=THEME)
        queue_embed.set_footer(
            text=f"Volume: {int(bot_vc.source.volume * 100)}%"
        )

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
    @leave.before_invoke
    @skip.before_invoke
    @volume.before_invoke
    async def ensure_voice(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        if author_vc := ctx.author.voice:
            if existing_vc := ctx.guild.voice_client:
                if existing_vc.channel.id != author_vc.channel.id:
                    await ctx.respond(
                        f"I'm already in {existing_vc.channel.mention}, please join that channel.",
                        ephemeral=True,
                    )
                    raise discord.ApplicationCommandError(
                        "Author not connected to bot's voice channel."
                    )

        else:
            await ctx.respond(
                "Please connect to a voice channel before using this command",
                ephemeral=True,
            )
            raise discord.ApplicationCommandError(
                "Author not connected to a voice channel."
            )


def setup(bot):
    bot.add_cog(SlashMusic(bot))
