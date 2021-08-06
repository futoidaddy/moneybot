import discord
from discord.ext import commands, tasks
import json
import os

class usercommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    

    # @commands.command()
    # async def balance(self, ctx, *, member: discord.Member): #could use converter on member


    @commands.Cog.listener()
    async def on_ready(self):
        print('user commands ready.')

def setup(client):
    client.add_cog(usercommands(client))