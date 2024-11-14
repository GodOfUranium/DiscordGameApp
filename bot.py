import os
import discord
from discord import app_commands, Embed
from discord.ui import View, Button
from dotenv import load_dotenv

# .env
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
# discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
"""
class YNView(View):
    def __init__(self, yesAction:str, noAction:str):
        super().__init__()
        self.yesButton = Button(label="Yes", style=discord.ButtonStyle.danger)
        self.noButton = Button(label="No", style=discord.ButtonStyle.success)
        self.add_item(self.yesButton)
        self.add_item(self.noButton)
    @yesButton.callback
    async def yesButton_clicked(self, ctx):"""


########### Commands ###########
# -------- /register -----------
@tree.command(
    name="register",
    description="Register yourself to play!"
)
async def register_command(ctx, username:str):
    # TODO: Register User to Database
    embed = Embed(
        title="/register",
        description=f"Successfully registered {username} to account {ctx.user.mention}",
        color=0x00ff00
    )
    await ctx.response.send_message(embed=embed)

# ------- /del_account ----------
@tree.command(
    name="del_account",
    description="Deletes your entire Account. WARNING: not reversible!"
)
async def del_account(ctx):
    embed = Embed(
        title="Are you sure?",
        description="Do you really want to delete all your account data?",
        color=0xffff00
    )
    yesButton = Button(label="Yes", style=discord.ButtonStyle.danger)
    noButton = Button(label="No", style=discord.ButtonStyle.success)
    async def yesButton_callback(ctx):
        yesButton.disabled = True
        noButton.disabled = True
        embed = Embed(
            title="/del_account",
            description="Successfully deleted account",
            color=0x00ff00
        )
        await ctx.response.edit_message(view=None, embed=embed)
        # TODO: Delete User from Database
    async def noButton_callback(ctx):
        yesButton.disabled = True
        noButton.disabled = True
        await ctx.response.edit_message(view=view)
    yesButton.callback = yesButton_callback
    noButton.callback = noButton_callback
    view = View()
    view.add_item(yesButton)
    view.add_item(noButton)
    
    await ctx.response.send_message(embed=embed, view=view)


########### on_ready ###########
@client.event
async def on_ready():
    print("Syncing Tree...")
    await tree.sync()
    print("Ready!")

client.run(token)
