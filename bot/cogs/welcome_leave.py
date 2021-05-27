import os
import discord
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw

from bot import MyBot
from bot.data import Data


class WelcomeLeave(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.theme_color = discord.Color.purple()
        self.assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "assets",
        )
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "cache",
        )

        self.default_welcome_msg = (
            lambda guild: f"Hello [mention], welcome to {guild.name}!"
        )
        self.default_leave_msg = lambda guild: (
            "Goodbye [member], " f"thanks for staying at {guild.name}!"
        )
        self.asset = lambda asset_name: os.path.join(
            self.assets_dir, asset_name
        )
        self.center_to_corner = lambda center_pos, size: (
            center_pos[0] - size[0] // 2,
            center_pos[1] - size[1] // 2,
        )

        # Make sure that cache dir exists
        if "cache" not in os.listdir(os.path.dirname(self.cache_dir)):
            os.mkdir(self.cache_dir)

    async def find_welcome_channel(
        self, guild: discord.Guild
    ) -> discord.TextChannel or None:
        channels: list[discord.TextChannel] = await guild.fetch_channels()

        for channel in channels:
            if "welcome" in channel.name:
                return channel

        return None

    async def find_leave_channel(
        self, guild: discord.Guild
    ) -> discord.TextChannel or None:
        channels: list[discord.TextChannel] = await guild.fetch_channels()

        for channel in channels:
            if "bye" in channel.name:
                return channel

        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild: discord.Guild = member.guild
        Data.check_guild_entry(guild)

        Data.c.execute(
            """SELECT welcome_message, welcome_channel, auto_role
            FROM guilds WHERE id = :guild_id""",
            {"guild_id": guild.id},
        )
        data = Data.c.fetchone()
        welcome_message = data[0]

        welcome_channel_id = data[1]

        if welcome_channel_id == "disabled":
            return

        if not welcome_channel_id:
            welcome_channel = await self.find_welcome_channel(guild)

            # Exit the function if no welcome channel is provided or
            # automatically found
            if not welcome_channel:
                return
        else:
            welcome_channel = guild.get_channel(int(welcome_channel_id))

        if data[2]:
            auto_role = guild.get_role(int(data[2]))
        else:
            auto_role = None

        if not welcome_message:
            welcome_message = self.default_welcome_msg(guild)

        # Replace placeholders with actual information
        welcome_message = welcome_message.replace("[mention]", member.mention)
        welcome_message = welcome_message.replace("[member]", str(member))
        welcome_message = welcome_message.replace("[server]", str(guild))

        # Get user's avatar
        avatar_path = os.path.join(self.cache_dir, f"pfp.jpg")
        await member.avatar_url.save(avatar_path)

        # Welcome image variables
        avatar_center_pos = (1920, 867)
        username_center_pos = (1920, 150)
        welcome_msg = "Welcome To"
        welcome_msg_center_pos = (1920, 1600)
        server_center_pos = (1920, 1900)

        # Prepare circle avatar
        im = Image.open(avatar_path)
        im = im.convert("RGB")
        im = im.resize((1024, 1024))
        bigsize = (im.size[0] * 3, im.size[1] * 3)
        mask = Image.new("L", bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(im.size, Image.ANTIALIAS)
        im.putalpha(mask)
        im.save(os.path.join(self.cache_dir, "lol.png"))

        # output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
        # output.putalpha(mask)
        # output.save(os.path.join(self.cache_dir, 'circle_pfp.png'))

        # Prepare welcome image
        w_img_path = os.path.join(self.cache_dir, "welcome.jpg")
        w_img = Image.open(self.asset("welcome_image.jpg"))
        avatar_corner_pos = self.center_to_corner(avatar_center_pos, im.size)
        w_img.paste(im, avatar_corner_pos, im)
        w_img_draw = ImageDraw.Draw(w_img)
        username_font = ImageFont.truetype(
            self.asset("montserrat_extrabold.otf"), 165
        )
        welcome_font = ImageFont.truetype(
            self.asset("earthorbiterxtrabold.ttf"), 250
        )
        server_font_size = 285

        # Make sure that server name doesnt overflow
        while True:
            server_font = ImageFont.truetype(
                self.asset("earthorbiterxtrabold.ttf"), server_font_size
            )
            server_bbox_size = server_font.getsize(guild.name)

            # Check whether text overflows
            if server_bbox_size[0] >= w_img.size[0]:
                server_font_size -= 5
            else:
                break

        # Add username to image
        username_size = username_font.getsize(str(member))
        username_corner_pos = self.center_to_corner(
            username_center_pos, username_size
        )
        w_img_draw.text(
            username_corner_pos,
            str(member),
            fill=(255, 255, 255),
            font=username_font,
        )

        # Add welcome message to image
        welcome_msg_size = welcome_font.getsize(welcome_msg)
        welcome_msg_corner_pos = self.center_to_corner(
            welcome_msg_center_pos, welcome_msg_size
        )
        w_img_draw.text(
            welcome_msg_corner_pos,
            welcome_msg,
            fill=(255, 255, 255),
            font=welcome_font,
        )

        # Add server name to image
        server_size = server_font.getsize(guild.name)
        server_corner_pos = self.center_to_corner(
            server_center_pos, server_size
        )
        w_img_draw.text(
            server_corner_pos,
            guild.name,
            fill=(255, 255, 255),
            font=server_font,
        )

        # Save the image to cache
        w_img.save(w_img_path)

        await welcome_channel.send(
            welcome_message, file=discord.File(w_img_path)
        )

        # Give auto role to new member if they are not a bot
        if not member.bot and auto_role:
            await member.add_roles(auto_role)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild: discord.Guild = member.guild
        Data.check_guild_entry(guild)

        Data.c.execute(
            """SELECT leave_message, leave_channel FROM guilds
            WHERE id = :guild_id""",
            {"guild_id": guild.id},
        )
        data = Data.c.fetchone()
        leave_message = data[0]
        leave_channel_id = data[1]

        if leave_channel_id == "disabled":
            return

        if not leave_channel_id:
            leave_channel = await self.find_leave_channel(guild)

            # Exit the function if no leave channel is provided or
            # automatically found
            if not leave_channel:
                return
        else:
            leave_channel = guild.get_channel(int(leave_channel_id))

        if not leave_message:
            leave_message = self.default_leave_msg(guild)

        # Replace placeholders with actual information
        leave_message = leave_message.replace("[member]", str(member))
        leave_message = leave_message.replace("[server]", str(guild))

        await leave_channel.send(leave_message)


def setup(bot):
    bot.add_cog(WelcomeLeave(bot))
