import os
import discord
import requests
from dotenv import load_dotenv

load_dotenv()
butler_token = os.getenv('BOT_TOKEN')
omdb_token = os.getenv('OMDB_API_KEY')
movie_endpoint = 'http://www.omdbapi.com/?apikey=' + omdb_token + '&t='
voice_connections = {}

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


@butler.slash_command()
async def record(ctx):
    voice = ctx.author.voice

    async def once_done(sink: discord.sinks, channel: discord.TextChannel,
                        *args):  # Our voice client already passes these in.
        recorded_users = [  # A list of recorded users
            f"<@{user_id}>"
            for user_id, audio in sink.audio_data.items()
        ]
        await sink.vc.disconnect()  # Disconnect from the voice channel.
        files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in
                 sink.audio_data.items()]  # List down the files.
        await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.",
                           files=files)  # Send a message with the accumulated files.

    if not voice:
        await ctx.respond("You aren't in a voice channel!")

    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    voice_connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.respond("Started recording!")


@butler.slash_command()
async def stop_recording(ctx):
    if ctx.guild.id in voice_connections:  # Check if the guild is in the cache.
        vc = voice_connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del voice_connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.delete()  # And delete.
    else:
        await ctx.respond("I am currently not recording here.")  # Respond with this if we aren't recording.


if __name__ == '__main__':
    butler.run(butler_token)
