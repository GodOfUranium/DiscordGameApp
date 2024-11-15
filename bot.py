import os
import json
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

########### Functions ##########
# -------- json server ---------
def createJson(guild):
    serverTemplate = {
        "guildName":guild.name,
        "accounts":[]
    }
    with open(f"data/{guild.id}.json", "w") as f:
        json.dump(serverTemplate, f, indent=4)

    print(f"\033[93m#\033[0m Added server {guild.id} ({guild.name}) to data directory. PATH: data/{guild.id}.json")

    return 1 # to ensure it completed running

# --------- json user ----------
def addUser(guild, username:str, linkedTo:str):
    user = {
        "username":username,
        "linkedTo":linkedTo,
        "cash":0,
        "inventory":[]
    }
    with open(f"data/{guild.id}.json", "r") as f:
        data = json.load(f)
    data["accounts"].append(user)
    with open(f"data/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"\033[93m+\033[0m Added account {username} (linked to {linkedTo}) to data/{guild.id}.json (connected to Server \"{guild.name}\")")

    return 1 # to ensure it completed running

# ------- get json user --------
def getUser(guild, linkedTo:str):
    with open(f"data/{guild.id}.json", "r") as f:
        data = json.load(f)
        for user in data["accounts"]:
            if(user["linkedTo"] == linkedTo):
                return user
        return None

########### Commands ###########
# -------- /register -----------
@tree.command(
    name="register",
    description="Register yourself to play!"
)
async def register_command(ctx, username:str=None):
    await ctx.response.defer()

    if(username==None):
        username=ctx.user.display_name

    try:
        open(f"data/{ctx.guild.id}.json")
    except FileNotFoundError:
        createJson(ctx.guild)==1
    finally:
        if(getUser(ctx.guild, ctx.user.name) == None):
            addUser(ctx.guild, username, ctx.user.name)==1
            embed = Embed(
                title="/register",
                description=f"Successfully registered {username} to account {ctx.user.mention}",
                color=0x00ff00
            )
        else:
            embed = Embed(
                title="/register",
                description="You can only create one account",
                color=0xff0000
            )
        await ctx.followup.send(embed=embed)

# ------- /del_account ----------
@tree.command(
    name="del_account",
    description="Deletes your entire Account. WARNING: not reversible!"
)
async def del_account(ctx):
    embed = Embed(
        title="Are you sure?",
        description="Do you really want to delete all your account data?",
        color=0xffff00)

    yesButton = Button(label="Yes", style=discord.ButtonStyle.danger)
    noButton = Button(label="No", style=discord.ButtonStyle.success)

    async def yesButton_callback(ctx):
        yesButton.disabled = True
        noButton.disabled = True
        
        # TODO: Delete User from Database
        
        embed = Embed(
            title="/del_account",
            description="Successfully deleted account",
            color=0x00ff00)
        
        await ctx.response.edit_message(view=None, embed=embed)
    
    async def noButton_callback(ctx):
        yesButton.disabled = True
        noButton.disabled = True
        embed = Embed(
            title="/del_account",
            description="Successfully canceled deletion",
            color=0x00ff00)
        await ctx.response.edit_message(view=None, embed=embed)
    
    yesButton.callback = yesButton_callback
    noButton.callback = noButton_callback

    view = View()
    view.add_item(yesButton)
    view.add_item(noButton)
    
    await ctx.response.send_message(embed=embed, view=view)

########### on_ready ###########
@client.event
async def on_ready():
    print("\033[94;1mSyncing Tree...\033[0m")
    await tree.sync()
    print("\033[92;1mReady!\033[0m")

client.run(token)
