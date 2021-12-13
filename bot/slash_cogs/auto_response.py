import json
import discord
from discord.ext import commands

from bot import TESTING_GUILDS, THEME
from bot.data import Data
from bot.utils import dbl_vote_required
from bot.views.confirm import ConfirmView


class SlashAutoResponse(commands.Cog):
    """
    Commands to make Sparta automatically reply to certain phrases
    """

    # TODO: Enable when removing prefix commands
    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author.bot:
    #         return

    #     Data.c.execute(
    #         "SELECT auto_responses FROM guilds WHERE id = :guild_id",
    #         {"guild_id": message.guild.id},
    #     )
    #     auto_resps = json.loads(Data.c.fetchone()[0])
    #     content: str = message.content
    #     channel: discord.TextChannel = message.channel

    #     if content in auto_resps:
    #         response = auto_resps[content]

    #         # Auto Response Variables
    #         response = response.replace("[member]", str(message.author))
    #         response = response.replace("[nick]", message.author.display_name)
    #         response = response.replace("[name]", message.author.name)

    #         await channel.send(
    #             response, allowed_mentions=discord.AllowedMentions.none()
    #         )

    @dbl_vote_required()
    @commands.slash_command(name="addautoresponse", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def add_auto_response(
        self, ctx: discord.ApplicationContext, activation: str, response: str
    ):
        """
        Add an auto response phrase. Variables you can use: [member], [nick], [name]
        """

        Data.check_guild_entry(ctx.guild)
        Data.c.execute(
            "SELECT auto_responses FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        current_auto_resps = json.loads(Data.c.fetchone()[0])

        if activation in current_auto_resps:
            confirm_view = ConfirmView()
            await ctx.respond(
                "An auto response with this activation already exists and will be overwritten by the new one. Do you want to continue?",
                view=confirm_view,
            )
            await confirm_view.wait()

            if not confirm_view.do_action:
                return

        current_auto_resps[activation] = response

        Data.c.execute(
            "UPDATE guilds SET auto_responses = :new_responses WHERE id = :guild_id",
            {
                "new_responses": json.dumps(current_auto_resps),
                "guild_id": ctx.guild.id,
            },
        )
        Data.conn.commit()

        ar_embed = discord.Embed(title="New Auto Response", color=THEME)
        ar_embed.add_field(name="Activation:", value=activation, inline=False)
        ar_embed.add_field(name="Response:", value=response, inline=False)
        await ctx.respond(embed=ar_embed)

    @commands.slash_command(
        name="removeautoresponse", guild_ids=TESTING_GUILDS
    )
    @commands.has_guild_permissions(administrator=True)
    async def remove_auto_response(
        self, ctx: discord.ApplicationContext, activation: str = None
    ):
        """
        Remove an auto response phrase
        """

        Data.check_guild_entry(ctx.guild)

        if activation:
            Data.c.execute(
                "SELECT auto_responses FROM guilds WHERE id = :guild_id",
                {"guild_id": ctx.guild.id},
            )
            current_auto_resps = json.loads(Data.c.fetchone()[0])

            if activation not in current_auto_resps:
                await ctx.respond(
                    "An auto response with this activation phrase does not exist"
                )
                return

            del current_auto_resps[activation]

            Data.c.execute(
                "UPDATE guilds SET auto_responses = :new_responses WHERE id = :guild_id",
                {
                    "new_responses": json.dumps(current_auto_resps),
                    "guild_id": ctx.guild.id,
                },
            )
            Data.conn.commit()
            await ctx.respond(
                f"Auto response with activation:```{activation}```has been removed"
            )

        else:
            confirm_view = ConfirmView()
            await ctx.respond(
                "You are about to delete all auto responses in this server. Do you want to continue?",
                view=confirm_view,
            )
            await confirm_view.wait()

            if confirm_view.do_action:
                Data.c.execute(
                    "UPDATE guilds SET auto_responses = '{}' WHERE id = :guild_id",
                    {"guild_id": ctx.guild.id},
                )
                Data.conn.commit()
                await ctx.respond(
                    "All auto responses in this server have been deleted"
                )

    @commands.slash_command(name="viewautoresponses", guild_ids=TESTING_GUILDS)
    async def view_auto_responses(self, ctx: discord.ApplicationContext):
        """
        See all the auto responses in the server
        """

        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "SELECT auto_responses FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        auto_resps = json.loads(Data.c.fetchone()[0])

        if auto_resps:
            auto_resps_embed = discord.Embed(
                title=f"Auto Responses in {ctx.guild}", color=THEME
            )

            for activation in auto_resps:
                response = auto_resps[activation]
                auto_resps_embed.add_field(
                    name=activation, value=response, inline=False
                )

            await ctx.respond(embed=auto_resps_embed)

        else:
            await ctx.respond("This server does not have any auto responses")


def setup(bot):
    bot.add_cog(SlashAutoResponse())
