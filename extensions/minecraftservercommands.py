import asyncio

import discord
from discord.ext import commands, tasks
import os
import boto3
from mcstatus import JavaServer

server_management_channel_id = 1119297287831691275


# Helper Functions
def in_channel(channel_id):
    async def predicate(ctx):
        return ctx.channel.id == channel_id

    return commands.check(predicate)


def get_ec2_instance_status(instance_id):
    client = boto3.client(
        'ec2',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION'))
    return client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name']


def handle_error(ctx, error):
    if isinstance(error, discord.errors.CheckFailure):
        return ctx.respond(
            embed=discord.Embed(
                title='Wrong channel',
                description=f"You can only use this command in <#{server_management_channel_id}>.",
                color=0xFF3838),
            ephemeral=True)
    else:
        return ctx.respond(
            embed=discord.Embed(
                title='Error',
                description=f"An error has occurred:\n{type(error)}\n{error}",
                color=0xFF3838),
            ephemeral=True)


# Main Cog
class MinecraftServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.instance_ID = os.getenv('MINECRAFT_EC2_INSTANCE_ID')
        self.server_ip = os.getenv('MINECRAFT_EC2_INSTANCE_IP')
        self.server_port = 8008
        self.server_watchdog.start()
        self.ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION'))

    def cog_unload(self):
        self.server_watchdog.cancel()

    @commands.slash_command(name="start_minecraft_server",
                            description="Starts the Minecraft server")
    @in_channel(server_management_channel_id)
    async def start_minecraft_server(self, ctx):
        response = self.ec2_client.start_instances(InstanceIds=[self.instance_ID])
        embed = discord.Embed(title="Server Status")
        if response['StartingInstances'][0]['CurrentState']['Name'] == 'pending':
            embed.description = 'Server is starting...'
            message = await ctx.respond(embed=embed)
            state = get_ec2_instance_status(self.instance_ID)
            while state == 'pending':
                await asyncio.sleep(5)
                state = get_ec2_instance_status(self.instance_ID)
            if state == 'running':
                embed.description = 'Server started.'
                embed.color = discord.Color.green()
            else:
                embed.description = 'Server failed to start.'
                embed.color = discord.Color.red()
            await message.edit_original_response(embed=embed)
        elif response['StartingInstances'][0]['CurrentState']['Name'] == 'running':
            embed.description = 'Server is already running.'
            embed.color = discord.Color.green()
            await ctx.respond(embed=embed)
        else:
            embed.description = 'Failed to start Server.'
            embed.color = discord.Color.red()
            await ctx.respond(embed=embed)

    @commands.slash_command(name="stop_minecraft_server",
                            description="Stops the Minecraft server")
    @in_channel(server_management_channel_id)
    async def stop_minecraft_server(self, ctx):
        response = self.ec2_client.stop_instances(InstanceIds=[self.instance_ID])
        embed = discord.Embed(title="Server Status")
        if response['StoppingInstances'][0]['CurrentState']['Name'] == 'stopping':
            embed.description = 'Server is shutting down...'
            message = await ctx.respond(embed=embed)
            state = get_ec2_instance_status(self.instance_ID)
            while state == 'stopping':
                await asyncio.sleep(5)
                state = get_ec2_instance_status(self.instance_ID)
            if state == 'stopped':
                embed.description = 'Server off.'
                embed.color = discord.Color.darker_gray()
            else:
                embed.description = 'Server failed to stop.'
                embed.color = discord.Color.red()
            await message.edit_original_response(embed=embed)

        elif response['StoppingInstances'][0]['CurrentState']['Name'] == 'stopped':
            embed.description = 'Server is already off.'
            embed.color = discord.Color.darker_gray()
            await ctx.respond(embed=embed)

        else:
            embed.description = 'Failed to stop Server.'
            embed.color = discord.Color.red()
            await ctx.respond(embed=embed)

    @commands.slash_command(name="server_status",
                            description="Checks the status of the Minecraft server")
    @in_channel(server_management_channel_id)
    async def minecraft_server_status(self, ctx):
        embed = discord.Embed(title="Server Status")
        status = get_ec2_instance_status(self.instance_ID)
        if status == 'running':
            embed.description = 'Server is running.\n'

            try:
                server = await JavaServer.async_lookup(f"{self.server_ip}:{self.server_port}")
                embed.color = discord.Color.green()
                if server.status().players.online == 0:
                    embed.description += "There are no players online."
                elif server.status().players.online == 1:
                    embed.description += f"{server.status().players.sample[0].name} is alone on the server."
                else:
                    embed.description += f"There is {server.status().players.online} player online."
                    embed.add_field(name="Online Players:",
                                    value='\n'.join([x.name for x in server.status().players.sample]),
                                    inline=False)
                await ctx.respond(embed=embed)
            except Exception as e:
                embed.description += f'Failed to fetch player list with error:\n{e}'
                embed.color = discord.Color.yellow()
                await ctx.respond(embed=embed)
        elif status == 'stopped':
            embed.description = 'Server is off.'
            embed.color = discord.Color.darker_gray()
            await ctx.respond(embed=embed)
        elif status == 'stopping':
            embed.description = 'Server is shutting down...'
            embed.color = discord.Color.dark_gray()
            await ctx.respond(embed=embed)
        elif status == 'pending':
            embed.description = 'Server is starting...'
            embed.color = discord.Color.blue()
            await ctx.respond(embed=embed)
        else:
            embed.description = 'Server is in an unknown state.\nServer state: ' + status
            embed.color = discord.Color.red()
            await ctx.respond(embed=embed)

        @commands.slash_command(name="get_server_info",
                                description="Gets the IP address and port of the Minecraft server")
        async def get_server_info(self, ctx):
            await ctx.respond(f'The Minecraft server IP address is {self.server_ip}', ephemeral=True)

    @commands.slash_command(name="ping_minecraft_server", description="Pings the Minecraft server")
    async def ping_minecraft_server(self, ctx):
        pass

    @start_minecraft_server.error
    async def start_minecraft_server_error(self, ctx, error):
        await handle_error(ctx, error)
        return

    @stop_minecraft_server.error
    async def stop_minecraft_server_error(self, ctx, error):
        await handle_error(ctx, error)
        return

    @minecraft_server_status.error
    async def minecraft_server_status_error(self, ctx, error):
        await handle_error(ctx, error)
        return

    @tasks.loop(minutes=60)
    async def server_watchdog(self):
        await self.bot.wait_until_ready()
        status = get_ec2_instance_status(self.instance_ID)
        if status == 'running':
            try:
                server = await JavaServer.async_lookup(f"{self.server_ip}:{self.server_port}")
                if server.status().players.online == 0:
                    channel = self.bot.get_channel(server_management_channel_id)
                    message = await channel.send(embed=discord.Embed(
                        title="Server Notification",
                        description="There are no players online. Shutting down server in 30 seconds unless a player connects.",
                        color=discord.Color.yellow()))
                    await asyncio.sleep(30)
                    server = await JavaServer.async_lookup(f"{self.server_ip}:{self.server_port}")
                    if server.status().players.online == 0:
                        # stop the server
                        response = self.ec2_client.stop_instances(InstanceIds=[self.instance_ID])
                        embed = discord.Embed(title="Server Status")
                        if response['StoppingInstances'][0]['CurrentState']['Name'] == 'stopping':
                            embed.description = 'Server is shutting down...'
                            embed.color = discord.Color.light_gray()
                            message = await message.edit(embed=embed)
                            state = get_ec2_instance_status(self.instance_ID)
                            while state == 'stopping':
                                await asyncio.sleep(5)
                                state = get_ec2_instance_status(self.instance_ID)
                            if state == 'stopped':
                                embed.description = 'Server off.'
                                embed.color = discord.Color.darker_gray()
                            else:
                                embed.description = 'Server failed to stop.'
                                embed.color = discord.Color.red()
                            await message.edit(embed=embed)
                    else:
                        pass
                else:
                    pass
            except Exception as e:
                print(e)
        elif status == 'stopped':
            pass


def setup(bot):
    bot.add_cog(MinecraftServerCommands(bot))
