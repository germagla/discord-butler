import os

from openai import OpenAI
from discord.ext import commands


class OpenAIText(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # self.embed = discord.Embed(title="ChatGPT says:", description="", color=0x10a37f)

    @commands.slash_command(name="ask_gpt3", description="Ask GPT3.5 a question")
    async def ask_gpt3(self, ctx, *, question):
        await ctx.defer()
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. "
                               "When asked a question you aim to answer it as best as you can "
                               "with a detailed and thorough answer. Your answer must not exceed 1900 characters."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        await ctx.respond(response.choices[0].message.content)

    @commands.slash_command(name="ask_gpt4", description="Ask GPT4 a question")
    async def ask_gpt4(self, ctx, *, question):
        await ctx.defer()
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. "
                               "When asked a question you aim to answer it as best as you can "
                               "with a detailed and thorough answer. Your answer must not exceed 1900 characters."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        await ctx.respond(response.choices[0].message.content)


def setup(bot):
    bot.add_cog(OpenAIText(bot))
