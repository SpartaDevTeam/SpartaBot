import os
import re
import asyncio
import wavelink
import discord
from discord.ext import commands, pages

from bot import TESTING_GUILDS, THEME


class SlashMusic(commands.Cog):
    """
    Jam to your favorite tunes with your favorite bot
    """

    # TODO: Add remove from queue, loop command

    song_queues: dict[int, asyncio.Queue[wavelink.YouTubeTrack]] = {}
    currently_playing: dict[int, wavelink.YouTubeTrack] = {}
    play_next: dict[int, asyncio.Event] = {}
    node_pool_connected = asyncio.Event()

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.node_pool_connected.clear()
        bot.loop.create_task(self.connect_nodes())

    def get_song_queue(
        self, ctx: discord.ApplicationContext
    ) -> asyncio.Queue[wavelink.YouTubeTrack]:
        guild_id: int = ctx.guild_id  # type: ignore

        if guild_id not in self.song_queues:
            # Guild queue does not exist, create a new one...
            self.song_queues[guild_id] = asyncio.Queue()
            self.play_next[guild_id] = asyncio.Event()
            self.play_next[guild_id].set()
            self.bot.loop.create_task(self.process_song_queue(ctx))

        return self.song_queues[guild_id]

    def get_track_embed(self, track: wavelink.YouTubeTrack) -> discord.Embed:
        clean_title = track.title.replace("`", "")
        duration_mins, duration_secs = (
            int(x) for x in divmod(track.duration, 60)
        )

        desc = f"\
            Title: `{clean_title}`\n\
            Author: `{track.author}`\n\
            Duration: `{duration_mins}:{duration_secs}`\
        "

        if uri := track.uri:
            desc += f"\n[YouTube Link]({uri})"

        em = discord.Embed(color=THEME, description=desc)
        em.set_image(url=track.thumbnail)
        return em

    async def connect_nodes(self):
        """Connect to Lavalink Nodes"""

        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=os.environ["LAVALINK_HOST"],
            port=int(os.environ["LAVALINK_PORT"]),
            password=os.environ["LAVALINK_PASSWORD"],
        )
        self.node_pool_connected.set()
        print("Connected to Lavalink!")

    async def get_voice_client(
        self, ctx: discord.ApplicationContext
    ) -> wavelink.Player:
        if ctx.voice_client:
            return ctx.voice_client  # type: ignore
        return await ctx.author.voice.channel.connect(cls=wavelink.Player)  # type: ignore

    async def process_song_queue(self, ctx: discord.ApplicationContext):
        guild_id: int = ctx.guild_id  # type: ignore

        while True:
            # Wait till next song should be played
            await self.play_next[guild_id].wait()

            # Fetch next song...
            next_track = await self.song_queues[guild_id].get()
            self.currently_playing[guild_id] = next_track

            # ...and play it
            vc = await self.get_voice_client(ctx)
            await vc.play(next_track)
            self.play_next[guild_id].clear()

            em = self.get_track_embed(next_track)
            em.title = "Now Playing"
            await ctx.channel.send(embed=em)  # type: ignore

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: wavelink.Player, track: wavelink.Track, reason
    ):
        # Next song should play now
        self.play_next[player.guild.id].set()

    @commands.slash_command(guilds_ids=TESTING_GUILDS)
    async def join(self, ctx: discord.ApplicationContext):
        """
        Make Sparta rejoin a voice channel, has no effect if already in a VC
        """

        if not ctx.voice_client:
            voice_ch: discord.VoiceChannel = ctx.author.voice.channel  # type: ignore
            await voice_ch.connect()
            await ctx.respond(f"Joining {voice_ch.mention}...", ephemeral=True)
        else:
            await ctx.respond(
                "I'm already in your voice channel.", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def play(self, ctx: discord.ApplicationContext, search: str):
        """
        Search a song by name or URL, and add it to the song queue
        """

        if not ctx.guild_id:
            return

        search_results = await wavelink.YouTubeTrack.search(search)

        if re.match(
            r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.be)\/.+$", search
        ):
            filtered_results = [t for t in search_results if t.uri == search]

            if filtered_results:
                search_track = filtered_results[0]
            else:
                await ctx.respond(
                    "No videos were found that matched the given URL!",
                    ephemeral=True,
                )
                return
        else:
            search_track = search_results[0]

        if not search_track:
            await ctx.respond(
                "Unable to find a track with the given search query/URL!",
                ephemeral=True,
            )
            return

        # Add track to the song queue
        await self.get_song_queue(ctx).put(search_track)

        em = self.get_track_embed(search_track)
        em.title = "Added to Song Queue"
        await ctx.respond(embed=em)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def skip(self, ctx: discord.ApplicationContext):
        """
        Skip the currently playing song
        """

        vc = await self.get_voice_client(ctx)
        await vc.stop()
        await ctx.respond("⏭️ Song has been skipped!")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def resume(self, ctx: discord.ApplicationContext):
        """
        Resume the song that was playing
        """

        if not ctx.guild:
            return

        if ctx.guild.voice_client:
            vc = await self.get_voice_client(ctx)

            if vc.is_paused():
                await vc.resume()
                await ctx.respond("▶️ Resuming the song...")
            else:
                await ctx.respond(
                    "The song is already playing...", ephemeral=True
                )

        else:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def pause(self, ctx: discord.ApplicationContext):
        """
        Pause the song that is playing
        """

        if not ctx.guild:
            return

        if ctx.guild.voice_client:
            vc = await self.get_voice_client(ctx)

            if not vc.is_paused():
                await vc.pause()
                await ctx.respond("⏸️ Pausing the song...")
            else:
                await ctx.respond(
                    "The song is already paused...", ephemeral=True
                )

        else:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def volume(self, ctx: discord.ApplicationContext, new_volume: int):
        """
        Set the music volume as a percentage
        """

        if not ctx.guild:
            return

        if ctx.guild.voice_client:
            new_volume = max(0, min(new_volume, 1000))
            vc = await self.get_voice_client(ctx)
            await vc.set_volume(new_volume)
            await ctx.respond(f"🔊 Volume changed to `{new_volume}%`")
        else:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def queue(self, ctx: discord.ApplicationContext):
        """
        View all the songs currently in the queue
        """

        if not (ctx.guild and ctx.guild_id):
            return

        if not ctx.guild.voice_client:
            await ctx.respond(
                "There isn't any music playing right now", ephemeral=True
            )
            return

        if (
            ctx.guild_id not in self.song_queues
            or ctx.guild_id not in self.currently_playing
        ):
            await ctx.respond(
                "The song queue is empty right now", ephemeral=True
            )
            return

        guild_queue = self.song_queues[ctx.guild_id]
        queue_list_copy: list[wavelink.YouTubeTrack] = []

        # Flush all tracks in queue and add them to a list
        while True:
            try:
                queue_list_copy.append(guild_queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        # Re-add all tracks from list to original queue
        for t in queue_list_copy:
            guild_queue.put_nowait(t)

        queue_embeds = []

        # Add current Track
        if current_track := self.currently_playing.get(ctx.guild_id):
            em = self.get_track_embed(current_track)
            em.title = "Currently Playing"
            queue_embeds.append(em)

        # Generate track embeds
        for i, track in enumerate(queue_list_copy):
            em = self.get_track_embed(track)
            noun = "song" if i == 0 else "songs"
            em.title = f"{i + 1} {noun} away..."
            queue_embeds.append(em)

        paginator = pages.Paginator(pages=queue_embeds)
        await paginator.respond(ctx.interaction)

    @join.before_invoke
    @play.before_invoke
    @skip.before_invoke
    @volume.before_invoke
    async def ensure_voice(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        await self.node_pool_connected.wait()  # Wait for lavalink nodes to connect

        if not ctx.guild:
            raise discord.ApplicationCommandError(
                "Music command was run outisde a guild."
            )

        if author_vc := ctx.author.voice:  # type: ignore
            if existing_vc := ctx.guild.voice_client:
                if existing_vc.channel.id != author_vc.channel.id:  # type: ignore
                    await ctx.respond(
                        f"I'm already in {existing_vc.channel.mention}, please join that channel.",  # type: ignore
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
