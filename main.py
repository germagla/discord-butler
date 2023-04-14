import os
import discord
import requests
from dotenv import load_dotenv

load_dotenv()
butler_token = os.getenv('BOT_TOKEN')
omdb_token = os.getenv('OMDB_API_KEY')
movie_endpoint = 'http://www.omdbapi.com/?apikey=' + omdb_token + '&t='

butler = discord.Bot()


@butler.event
async def on_ready():
    print(f'Logged in as {butler.user} (ID: {butler.user.id})')


@butler.slash_command()
async def ping(ctx):
    await ctx.respond('pong')


@butler.slash_command()
async def movie(ctx, movie_name: str):
    # movie_name = ' '.join(movie_name)

    response = requests.get(movie_endpoint + movie_name)
    if response.status_code == 200:
        movie_json = response.json()
        if response.json()['Response'] == 'False':
            await ctx.respond('A movie with that name does not exist. Please try again. (The API says so, don\'t @ me)')
            return
        movie_formatting = f'''
Poster URL: {movie_json['Poster']}
```
Title: {movie_json['Title']}
Year: {movie_json['Year']}
imdbRating: {movie_json['imdbRating']}
imdbID: {movie_json['imdbID']}
Rated: {movie_json['Rated']}
Runtime: {movie_json['Runtime']} 
Genre: {movie_json['Genre']}
Director: {movie_json['Director']} 
Writer: {movie_json['Writer']} 
Actors: {movie_json['Actors']} 
Plot: {movie_json['Plot']} 

```
        '''
        await ctx.respond(movie_formatting)

    else:
        await ctx.respond('krakrak. POOF! Something went wrong, please try again later')


if __name__ == '__main__':
    butler.run(butler_token)
