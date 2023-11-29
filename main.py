import asyncio
import os
import discord
from dotenv import load_dotenv

load_dotenv()

butler = discord.Bot()


@butler.event
async def on_ready():
    await butler.sync_commands()
    print(f'Logged in as {butler.user.name} (ID: {butler.user.id})')
    print(f'{len(butler.guilds)} servers connected: {", ".join([guild.name for guild in butler.guilds])}')


@butler.slash_command(name="ping", description="Returns the latency of the bot")
async def ping(ctx):
    latency = round(butler.latency * 1000, 2)
    await ctx.respond(f'Pong! ({latency}ms)', ephemeral=True)


async def load_extensions():
    for filename in os.listdir('extensions'):
        if filename.endswith('.py'):
            butler.load_extension(f'extensions.{filename[:-3]}')
            print(f'Loaded {filename[:-3]} extension')


async def bot_start():
    await load_extensions()
    await butler.start(os.getenv('BOT_TOKEN'))


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot_start())
    except discord.LoginFailure:  # Add exception handling for failed login
        print("Invalid bot token")
    except KeyboardInterrupt:  # The bot will keep running until a KeyboardInterrupt
        print("Bot stopped.")
    finally:
        loop.close()


if __name__ == '__main__':
    main()
