# SpartaBot

A complete rewrite from scratch of the [Original Sparta Bot](https://github.com/SpartaDevTeam/Old-Sparta-Bot), using better technologies.
Moderation, automod, welcome and leave message, reaction roles, fun commands, etc., just some of the stuff that Sparta Bot offers.

## How to run

1. Install the dependencies in `requirements.txt` normally and `requirements_no_deps.txt` with pip's `--no-deps` flag. The `install_deps.sh` script does exactly this and was made for convenience.
2. Add the following environment variables to a `.env` file in the root directory:
    - `TOKEN` - Your Discord Bot Token.
    - `URBAN_API_KEY` - API key for accessing Urban Dictionary's API.
    - `DBL_TOKEN` - Top.gg bot token for receiving vote data.
    - `TESTING_GUILDS` (Optional) - Comma (,) separated string of guild IDs for testing `/` commands. Only applicable when running with `--debug` flag.
    - `DB_URI` - URI string of your database. You may have to install additional modules if you're using something other than PostgreSQL.
3. Run the command `alembic upgrade head` to run database migrations.
4. Run `python run.py` to start the bot. You can run the command with `--debug` flag to run in debug mode.

## Links

1. [Sparta](https://discord.com/api/oauth2/authorize?client_id=731763013417435247&permissions=8&scope=bot%20applications.commands)
2. [Sparta Beta](https://discord.com/api/oauth2/authorize?client_id=775798822844629013&permissions=8&scope=applications.commands%20bot)
3. [Top.gg](https://top.gg/bot/731763013417435247)
4. [Bots for Discord](https://botsfordiscord.com/bot/731763013417435247)
5. [Support Server](https://discord.gg/RrVY4bP)
