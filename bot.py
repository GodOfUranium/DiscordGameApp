import os
import json
import discord
from discord import app_commands, Embed
from discord.ui import View, Button
from dotenv import load_dotenv

import inspect  # for logging in registerServer() / createJson()

# .env
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
# discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

########### Functions ##########
# ------ register server -------
async def registerServer(guild:discord.guild):
    try:
        open(f"data/{guild.id}.json")
    except FileNotFoundError:
        createJson(guild)

# ------ add server json -------
def createJson(guild:discord.guild):
    serverTemplate = {
        "guildName":guild.name,
        "users":[]
    }
    with open(f"data/{guild.id}.json", "w") as f:
        json.dump(serverTemplate, f, indent=4)

    caller_name = inspect.stack()[2].function   # for logging
    print(f"\033[92m#\033[0m Added server {guild.id} ({guild.name}) to data directory. PATH: data/{guild.id}.json (called by {caller_name})")

# ----- add user to json -------
def addUser(guild:discord.Guild, username:str, linkedTo:int):
    user = {
        "username":username,
        "linkedTo":linkedTo,
        "cash":0,
        "inventory":[]
    }
    with open(f"data/{guild.id}.json", "r") as f:
        data = json.load(f)
    data["users"].append(user)
    with open(f"data/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"\033[92m+\033[0m Added user {username} (linked to {linkedTo}) to data/{guild.id}.json (connected to Server \"{guild.name}\")")

# ----- get user from json -----
def getUser(guild:discord.Guild, linkedTo:int):
    with open(f"data/{guild.id}.json", "r") as f:
        data = json.load(f)
    for user in data["users"]:
        if(user["linkedTo"] == linkedTo):
            return user
    return None

# --- delete user from json -----
def deleteUser(guild:discord.Guild, linkedTo:int):
    with open(f"data/{guild.id}.json", "r") as f:
        data = json.load(f)
    targetDict = getUser(guild, linkedTo)
    for i, d in enumerate(data["users"]):
        if d == targetDict:
            data["users"].remove(d)
            break
    with open(f"data/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)
    print(f"\033[91m-\033[0m Removed user {targetDict["username"]} (linked to {linkedTo}) from users in data/{guild.id}.json (connected to Server \"{guild.name}\")")

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

    await registerServer(ctx.guild)

    if(getUser(ctx.guild, ctx.user.id) == None):
        addUser(ctx.guild, username, ctx.user.id)
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
async def del_account_command(ctx):
    await ctx.response.defer()

    await registerServer(ctx.guild)

    if(getUser(ctx.guild, ctx.user.id) != None):
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

            if(getUser(ctx.guild, ctx.user.id) != None):
                deleteUser(ctx.guild, ctx.user.id)
                embed = Embed(
                    title="/del_account",
                    description="Successfully deleted account",
                    color=0x00ff00
                )
            else:
                embed = Embed(
                    title="/del_account",
                    description="Your account has already been deleted",
                    color=0x3e1c00
                )

            await ctx.response.edit_message(view=None, embed=embed)
        
        async def noButton_callback(ctx):
            yesButton.disabled = True
            noButton.disabled = True

            if(getUser(ctx.guild, ctx.user.id) != None):
                embed = Embed(
                    title="/del_account",
                    description="Successfully canceled deletion",
                    color=0x00ff00
                )
            else:
                embed = Embed(
                    title="/del_account",
                    description="Your account has already been deleted",
                    color=0x3e1c00
                )

            await ctx.response.edit_message(view=None, embed=embed)
        
        yesButton.callback = yesButton_callback
        noButton.callback = noButton_callback

        view = View()
        view.add_item(yesButton)
        view.add_item(noButton)
        await ctx.followup.send(embed=embed, view=view)
    else:
        embed = Embed(
            title="/del_account",
            description="You can't delete an account if you don't have one",
            color=0xff0000
        )
        await ctx.followup.send(embed=embed)

# ----------- /shop -------------
@tree.command(
    name="shop",
    description="Opens shop"
)
async def shop_command(ctx):
    await registerServer(ctx.guild)

    await ctx.response.defer()
    if(getUser(ctx.guild, ctx.user.id) != None):
        embed = Embed(
            title="Shop",
            description="Shop page"
        )
        await ctx.followup.send(embed=embed)
    else:
        embed = Embed(
            title="/shop",
            description="You need to register to open the shop",
            color=0xff0000
        )
        await ctx.followup.send(embed=embed)

########### on_ready ###########
@client.event
async def on_ready():
    print("\033[94;1mSyncing Tree...\033[0m")
    await tree.sync()
    print("\033[92;1mReady!\033[0m")

client.run(token)
