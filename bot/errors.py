from discord.ext.commands.errors import CheckFailure


class DBLVoteRequired(CheckFailure):
    def __init__(self):
        super().__init__(
            "You must vote for the bot on Top.gg to use this command."
        )
