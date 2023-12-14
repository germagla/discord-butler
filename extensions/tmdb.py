import datetime
import os
import time

import discord
import requests
from discord import Color, Embed, SelectOption, ui
from discord.ext import commands

headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + os.getenv('TMDB_ACCESS_TOKEN')
}


def get_movie_details(movie_id):
    # Implementation for fetching movie details
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    response = requests.get(url, headers=headers)
    movie_details = response.json()
    return movie_details


def search_movie(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_name}&include_adult=true&language=en-US&page=1"

    response = requests.get(url, headers=headers)
    response = response.json()

    return response['results']


def to_discord_timestamp(date_str):
    """
    Convert a date string to a Discord-friendly timestamp.

    Args:
    date_str (str): A date string in the format "YYYY-MM-DD".

    Returns:
    str: A Discord-friendly timestamp string.
    """
    try:
        # Convert to a datetime object
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        # Convert to Unix timestamp
        unix_timestamp = int(time.mktime(date_obj.timetuple()))

        # Format for Discord
        discord_timestamp = f"<t:{unix_timestamp}>"
        return discord_timestamp
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."


class MovieCog(commands.Cog):
    def __init__(self, bot):
        self.select = None
        self.bot = bot

    async def select_callback(self, interaction: discord.Interaction):
        selected_movie_id = self.select.values[0]
        # await interaction.response.defer()

        detailed_info = get_movie_details(selected_movie_id)
        embed = discord.Embed(title=detailed_info['original_title'],
                              description=detailed_info['overview'],
                              color=Color.dark_teal(),
                              url=detailed_info['homepage'])
        embed.set_image(url='https://image.tmdb.org/t/p/w500/' + detailed_info['backdrop_path'])
        embed.set_thumbnail(url='https://image.tmdb.org/t/p/w500/' + detailed_info['poster_path'])
        embed.add_field(name="Release Date", value=to_discord_timestamp(detailed_info['release_date']), inline=False)
        await interaction.response.edit_message(embed=embed, view=None)

    @commands.slash_command(name="movie", description="Search for a movie")
    async def movie(self, ctx, title: str):
        movie_list = search_movie(title)[:10]

        if not movie_list:
            await ctx.respond(f"No movies found for '{title}'.", ephemeral=True)
            return

        embed = Embed(title=f"Search Results for '{title}'",
                      description="Choose a movie from the dropdown menu", color=Color.blurple())

        options = []
        for movie in movie_list:
            year = movie['release_date'].split('-')[0]
            options.append(SelectOption(label=movie['original_title'], description=year, value=str(movie['id'])))
            embed.add_field(name=movie['title'], value=f"{year}", inline=False)

        self.select = ui.Select(placeholder="Choose a movie", options=options)

        self.select.callback = self.select_callback

        view = ui.View()
        view.add_item(self.select)
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(MovieCog(bot))
