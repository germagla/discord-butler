import io
import os
import discord
import openai
import pydub
import requests
import logging
import discord.opus
from dotenv import load_dotenv
from io import BytesIO

# discord.opus.load_opus('libopus.so')
load_dotenv()
butler_token = os.getenv('BOT_TOKEN')
omdb_token = os.getenv('OMDB_API_KEY')
movie_endpoint = 'http://www.omdbapi.com/?apikey=' + omdb_token + '&t='
active_guilds = [os.getenv('GERMAGLA_BATCAVE_GUILD_ID', )]
openai.api_key = os.getenv('OPENAI_API_KEY')
WHISPER_ENGINE = os.getenv('WHISPER_ENGINE', 'davinci-codex')
voice_connections = {}

butler = discord.Bot()


@butler.event
async def on_ready():
    print(f'Logged in as {butler.user} (ID: {butler.user.id})')
    print(f'{len(butler.guilds)} guilds connected: {", ".join([guild.name for guild in butler.guilds])}')


@butler.slash_command()
async def ping(ctx):
    await ctx.respond('pong')


@butler.slash_command()
async def movie(ctx, title: str):
    response = requests.get(movie_endpoint + title)
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


async def finished_recording_callback(sink, channel: discord.TextChannel, *args):
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]

    await sink.vc.disconnect()
    # files = [
    #     discord.File(audio.file, f"{user_id}.{sink.encoding}")
    #     for user_id, audio in sink.audio_data.items()
    # ]
    voices = []
    for user_id, audio in sink.audio_data.items():
        user = await butler.fetch_user(user_id)
        voices.append(discord.File(audio.file, f"{user.name}.{sink.encoding}"))

    await channel.send(
        f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=voices
    )


@butler.command()
async def record(ctx):
    """Record your voice!"""
    voice = ctx.author.voice

    if not voice:
        return await ctx.respond("You're not in a vc right now")

    vc = await voice.channel.connect()
    voice_connections.update({ctx.guild.id: vc})

    vc.start_recording(
        discord.sinks.MP3Sink(),
        finished_recording_callback,
        ctx.channel,
    )

    await ctx.respond("The recording has started!")


@butler.command()
async def record_and_transcribe(ctx):
    voice = ctx.author.voice

    async def once_done(sink: discord.sinks, channel: discord.TextChannel,
                        *args):  # Our voice client already passes these in.
        recorded_users = [  # A list of recorded users
            f"<@{user_id}>"
            for user_id, audio in sink.audio_data.items()
        ]
        await sink.vc.disconnect()  # Disconnect from the voice channel.

        for user_id, audio in sink.audio_data.items():
            audio_data = pydub.AudioSegment.from_file_using_temporary_files(audio.file)
            audio_data = audio_data[:60000]  # 1 minute
            audio_data.export(f'{user_id}.{sink.encoding}')
            audio_file = open(f'{user_id}.{sink.encoding}', 'rb')
            transcript = openai.Audio.transcribe('whisper-1', audio_file)
            await ctx.send(f'<@{user_id}>: {transcript.text}')
            if os.path.exists(f'{user_id}.{sink.encoding}'):
                os.remove(f'{user_id}.{sink.encoding}')

        await channel.send(
            f"Finished recording audio for: {', '.join(recorded_users)}.")  # Send a message with the accumulated files.

    if not voice:
        await ctx.respond("You aren't in a voice channel!")

    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    voice_connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.MP3Sink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.respond("Started recording!")


# @butler.command()
# async def transcribe(ctx):
#     async def once_done(sink: discord.sinks, channel: discord.TextChannel,
#                         *args):  # Our voice client already passes these in.
#         recorded_users = [  # A list of recorded users
#             f"<@{user_id}>"
#             for user_id, audio in sink.audio_data.items()
#         ]
#         await sink.vc.disconnect()  # Disconnect from the voice channel.
#         # files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in
#         #          sink.audio_data.items()]  # List down the files.
#         # await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.",
#         #                    files=files)  # Send a message with the accumulated files.
#
#     # check if the user is in a voice channel
#     if ctx.author.voice and ctx.author.voice.channel:
#         # join the voice channel
#         voice_client = await ctx.author.voice.channel.connect()
#         # create a source object to receive audio from the voice channel
#         source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source=voice_client.start_recording(
#             discord.sinks.WaveSink(),  # The sink type to use.
#             once_done,  # What to do once done.
#             ctx.channel  # The channel to disconnect from.
#         )))
#         # create an audio segment object to store the audio data
#         audio_segment = pydub.AudioSegment.empty()
#         # loop until the voice client is disconnected or the command is stopped
#         while voice_client.is_connected() and not ctx.bot.loop.is_closed():
#             # read 20 milliseconds of audio data from the source
#             data = source.read()
#             # append the data to the audio segment object
#             audio_segment += pydub.AudioSegment(data=data, sample_width=2, frame_rate=48000, channels=2)
#             # check if the audio segment is longer than 5 seconds
#             if len(audio_segment) > 5000:
#                 # convert the audio segment to opus format and get the raw data
#                 opus_data = audio_segment.set_frame_rate(16000).set_channels(1).export(format="opus").read()
#                 # create a whisper request object with the opus data and the engine
#                 # whisper_request = openai.WhisperRequest(data=opus_data, engine=WHISPER_ENGINE)
#                 # try:
#                 #     # send the whisper request and get the response
#                 #     response = openai.Whisper.create(whisper_request)
#                 #     # get the transcription from the response
#                 #     transcription = response.transcription
#                 #     # send the transcription to the text channel
#                 #     await ctx.send(transcription)
#                 #     print(transcription)
#                 #
#                 # except openai.error.OpenAIError as e:
#                 #     # log the error message
#                 #     print(f"Whisper API error: {e}")
#
#                 transcript = openai.Audio.transcribe("whisper-1", opus_data)
#                 await ctx.respond(transcript)
#                 # clear the audio segment object for the next iteration
#                 audio_segment = pydub.AudioSegment.empty()
#
#     else:
#         # send an error message if the user is not in a voice channel
#         await ctx.send("You need to be in a voice channel to use this command.")


@butler.slash_command()
async def stop_listening(ctx):
    if ctx.guild.id in voice_connections:  # Check if the guild is in the cache.
        vc = voice_connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del voice_connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.delete()  # And delete.
    else:
        await ctx.respond(
            "I am currently not in a voice channel on this server.")  # Respond with this if we aren't recording.


if __name__ == '__main__':
    butler.run(butler_token)
