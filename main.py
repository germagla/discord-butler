import os
import discord
from dotenv import load_dotenv

load_dotenv()
butler_token = os.getenv('BOT_TOKEN')
butler = discord.Bot()


@butler.event
async def on_ready():
    print(f'Logged in as {butler.user} (ID: {butler.user.id})')


@butler.slash_command()
async def ping(ctx):
    await ctx.respond('pong')


if __name__ == '__main__':
    butler.run(butler_token)
