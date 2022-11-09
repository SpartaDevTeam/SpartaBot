import os
import re
import asyncio
import wavelink
import discord
from discord.ext import commands

from bot import TESTING_GUILDS, THEME


class SlashMusic(commands.Cog):
    """
    Jam to your favorite tunes with your favorite bot
    """

    # TODO: Add remove from queue, loop command

    song_queues: dict[int, asyncio.Queue[wavelink.YouTubeTrack]] = {}
    play_next: dict[int, asyncio.Event] = {}
    node_pool_connected = asyncio.Event()

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.node_pool_connected.clear()
        bot.loop.create_task(self.connect_nodes())

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

    def get_song_queue(
        self, guild_id: int
    ) -> asyncio.Queue[wavelink.YouTubeTrack]:
        if guild_id not in self.song_queues:
            # Guild queue does not exist, create a new one...
            self.song_queues[guild_id] = asyncio.Queue()

        return self.song_queues[guild_id]

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

        # Make sure bot has joined a voice channel
        await self.get_voice_client(ctx)
        await self.get_song_queue(ctx.guild_id).put(search_track)

        em = discord.Embed(
            title="Added to Song Queue",
            color=THEME,
        )
        em.add_field(name="Title", value=search_track.title)
        em.add_field(name="Author", value=str(search_track.author))
        em.set_thumbnail(url=search_track.thumbnail)
        await ctx.respond(embed=em)

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

        guild_queue = self.song_queues.get(ctx.guild_id)
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
