import os
import re
import uuid
import asyncio
import wavelink
import discord
from typing import Iterable
from discord.ext import commands, pages
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot import TESTING_GUILDS, THEME
from bot.db import async_session, models
from bot.views import ConfirmView


class SlashMusic(commands.Cog):
    """
    Jam to your favorite tunes with your favorite bot
    """

    # TODO: Add remove from queue, loop command

    song_queues: dict[int, asyncio.Queue[wavelink.YouTubeTrack]] = {}
    currently_playing: dict[int, wavelink.YouTubeTrack] = {}
    play_next: dict[int, asyncio.Event] = {}
    node_pool_connected = asyncio.Event()

    music_group = discord.SlashCommandGroup(
        name="music", guild_ids=TESTING_GUILDS
    )
    playlist_group = music_group.create_subgroup(
        name="playlist", guild_ids=TESTING_GUILDS
    )

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
        duration_str = (
            f"{duration_mins}:{duration_secs}"
            if duration_secs > 9
            else f"{duration_mins}:0{duration_secs}"
        )

        desc = f"\
            Title: `{clean_title}`\n\
            Author: `{track.author}`\n\
            Duration: `{duration_str}`\
        "

        if uri := track.uri:
            desc += f"\n[YouTube Link]({uri})"

        em = discord.Embed(color=THEME, description=desc)
        em.set_image(url=track.thumbnail)
        return em

    async def playlist_autocomplete(
        self, ctx: discord.AutocompleteContext
    ) -> list[str]:
        if not ctx.interaction.user:
            return []

        async with async_session() as session:
            query = select(models.Playlist).where(
                models.Playlist.owner_id == ctx.interaction.user.id
            )
            playlists: Iterable[models.Playlist] = await session.scalars(query)

            playlist_lst = [
                str(playlist.id)
                for playlist in playlists
                if not ctx.value
                or ctx.value in playlist.name
                or ctx.value in playlist.id
            ]
            return playlist_lst

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

    async def search_for_youtube_track(
        self, search_query: str
    ) -> wavelink.YouTubeTrack | None:
        search_results = await wavelink.YouTubeTrack.search(search_query)

        if re.match(
            r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.be)\/.+$", search_query
        ):
            for t in search_results:
                if t.uri == search_query:
                    return t

        elif search_results:
            return search_results[0]

        return None

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

    @music_group.command()
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

    @music_group.command()
    @discord.option(
        "search", description="A search query or a YouTube video's URL"
    )
    async def play(self, ctx: discord.ApplicationContext, search: str):
        """
        Search a song by name or URL, and add it to the song queue
        """

        if not ctx.guild_id:
            return

        search_track = await self.search_for_youtube_track(search)

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

    @music_group.command()
    async def skip(self, ctx: discord.ApplicationContext):
        """
        Skip the currently playing song
        """

        vc = await self.get_voice_client(ctx)
        await vc.stop()
        await ctx.respond("⏭️ Song has been skipped!")

    @music_group.command()
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

    @music_group.command()
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

    @music_group.command()
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

    @music_group.command()
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

    @playlist_group.command(name="create")
    async def create_playlist(
        self, ctx: discord.ApplicationContext, name: str
    ):
        """
        Create a new custom playlist
        """

        if not ctx.author:
            return

        async with async_session() as session:
            new_playlist_id = uuid.uuid4()
            new_playlist = models.Playlist(
                id=new_playlist_id.hex, owner_id=ctx.author.id, name=name
            )
            session.add(new_playlist)
            await session.commit()

            em = discord.Embed(title="Created new playlist", color=THEME)
            em.add_field(name="Playlist ID", value=f"`{new_playlist.id}`")
            em.add_field(name="Playlist Name", value=str(new_playlist.name))

        await ctx.respond(embed=em)

    @playlist_group.command(name="delete")
    @discord.option("playlist_id", autocomplete=playlist_autocomplete)
    async def delete_playlist(
        self, ctx: discord.ApplicationContext, playlist_id: str
    ):
        """
        Delete an existing custom playlist
        """

        if not ctx.author:
            return

        async with async_session() as session:
            query = (
                select(models.Playlist)
                .where(models.Playlist.id == playlist_id)
                .where(models.Playlist.owner_id == ctx.author.id)
                .options(selectinload(models.Playlist.songs))
            )
            playlist: models.Playlist | None = await session.scalar(query)

            if not playlist:
                await ctx.respond(
                    "The playlist with the given ID doesn't exist or isn't owned by you.",
                    ephemeral=True,
                )
                return

            em = discord.Embed(
                title="Delete Playlist?",
                color=THEME,
                description="This action cannot be undone!",
            )
            em.add_field(name="Playlist ID", value=f"`{playlist.id}`")
            em.add_field(name="Playlist Name", value=str(playlist.name))
            em.add_field(name="Songs Count", value=str(len(playlist.songs)))

            confirm_view = ConfirmView(
                ctx.author.id,
                confirm_msg="Playlist has been deleted!",
                cancel_msg="Cancelling playlist deletion...",
            )
            await ctx.respond(embed=em, view=confirm_view)

            # Delete original message if view timed out
            if await confirm_view.wait():
                await ctx.delete()
                return

            if confirm_view.do_action:
                # Delete all songs from playlist first...
                await asyncio.gather(
                    session.delete(song) for song in playlist.songs
                )

                # ...then delete the playlist itself
                await session.delete(playlist)

                await session.commit()

    @playlist_group.command(name="add")
    @discord.option("playlist_id", autocomplete=playlist_autocomplete)
    @discord.option(
        "song_query", description="A search query or a YouTube video's URL"
    )
    async def add_song_to_playlist(
        self,
        ctx: discord.ApplicationContext,
        playlist_id: str,
        song_query: str,
    ):
        """
        Add a song to custom playlist
        """

        if not ctx.author:
            return

        search_track = await self.search_for_youtube_track(song_query)

        if not search_track:
            await ctx.respond(
                "Unable to find a track with the given search query/URL!",
                ephemeral=True,
            )
            return

        async with async_session() as session:
            playlist_query = (
                select(models.Playlist)
                .where(models.Playlist.id == playlist_id)
                .where(models.Playlist.owner_id == ctx.author.id)
            )
            playlist: models.Playlist | None = await session.scalar(
                playlist_query
            )

            if not playlist:
                await ctx.respond(
                    "The playlist with the given ID doesn't exist or isn't owned by you.",
                    ephemeral=True,
                )
                return

            existing_song = await session.get(
                models.PlaylistSong, (search_track.uri, playlist.id)
            )
            if existing_song:
                await ctx.respond(
                    "This song is already in this playlist.", ephemeral=True
                )
                return

            new_song = models.PlaylistSong(
                uri=search_track.uri, playlist=playlist
            )
            session.add(new_song)
            await session.commit()

            em = self.get_track_embed(search_track)
            em.title = "Added Song to Playlist"
            em.color = discord.Color.green()
            em.add_field(
                name="Playlist",
                value=f"ID: `{playlist.id}`\nName: `{playlist.name}`",
            )

        await ctx.respond(embed=em)

    @playlist_group.command(name="remove")
    @discord.option("playlist_id", autocomplete=playlist_autocomplete)
    @discord.option(
        "song_query", description="A search query or a YouTube video's URL"
    )
    async def remove_song_from_playlist(
        self,
        ctx: discord.ApplicationContext,
        playlist_id: str,
        song_query: str,
    ):
        """
        Remove a song from custom playlist
        """

        if not ctx.author:
            return

        search_track = await self.search_for_youtube_track(song_query)

        if not search_track:
            await ctx.respond(
                "Unable to find a track with the given search query/URL!",
                ephemeral=True,
            )
            return

        async with async_session() as session:
            playlist_song_query = (
                select(models.PlaylistSong)
                .join(models.Playlist)
                .where(models.PlaylistSong.uri == search_track.uri)
                .where(models.PlaylistSong.playlist_id == playlist_id)
                .where(models.Playlist.owner_id == ctx.author.id)
                .options(selectinload(models.PlaylistSong.playlist))
            )
            playlist_song: models.PlaylistSong | None = await session.scalar(
                playlist_song_query
            )

            if not playlist_song:
                await ctx.respond(
                    "The given song is not in this playlist, or the playlist is not accessible (provide the song's URL for best results)",
                    ephemeral=True,
                )
                return

            em = self.get_track_embed(search_track)
            em.title = "Removed Song From Playlist"
            em.color = discord.Color.brand_red()
            em.add_field(
                name="Playlist",
                value=f"ID: `{playlist_song.playlist.id}`\nName: `{playlist_song.playlist.name}`",
            )

            await session.delete(playlist_song)
            await session.commit()

        await ctx.respond(embed=em)

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
