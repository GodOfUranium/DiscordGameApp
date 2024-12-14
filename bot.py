import os
import json
import logging
import logging.handlers
import discord
from discord import app_commands, Embed
from discord.ui import View, Button
from dotenv import load_dotenv

import inspect  # for logging in registerServer() / createJson()

"""
TODO LIST:
  * TODO finish /mine
"""

# logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='data/logs/discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
date_format = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', date_format, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        open(f"data/guilds/{guild.id}.json")
    except FileNotFoundError:
        createJson(guild)

# ------ add server json -------
def createJson(guild:discord.guild):
    serverTemplate = {
        "guildName":guild.name,
        "users":[]
    }
    with open(f"data/guilds/{guild.id}.json", "w") as f:
        json.dump(serverTemplate, f, indent=4)

    caller_name = inspect.stack()[2].function   # for logging
    logger.info(f"# Added server {guild.id} ({guild.name}) to data directory. PATH: data/guilds/{guild.id}.json (called by {caller_name})")

# ----- add user to json -------
def addUser(guild:discord.Guild, username:str, linkedTo:int):
    user = {
        "username":username,
        "linkedTo":linkedTo,
        "cash":0,
        "mineLevel":0,
        "inventory":[]
    }
    with open(f"data/guilds/{guild.id}.json", "r") as f:
        data = json.load(f)
    data["users"].append(user)
    with open(f"data/guilds/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)

    logger.info(f"+ Added user {username} (linked to {linkedTo}) to data/guilds/{guild.id}.json (connected to Server \"{guild.name}\")")

# ---- add item to inventory ----
def addItem(guild:discord.Guild, linkedTo:int, item:dict):
    with open(f"data/guilds/{guild.id}.json", "r") as f:
        data = json.load(f)
    data["users"][getUser(guild=guild,linkedTo=linkedTo, getPos=True)]["inventory"].append(item)
    with open(f"data/guilds/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)

# ----- get user from json ------
def getUser(guild:discord.Guild, linkedTo:int, getPos:bool=False):
    with open(f"data/guilds/{guild.id}.json", "r") as f:
        data = json.load(f)
    for i in range(len(data["users"])):
        user = data["users"][i]
        if(user["linkedTo"] == linkedTo):
            if(getPos):
                return i
            return user
    return None

# --- delete user from json -----
def deleteUser(guild:discord.Guild, linkedTo:int):
    with open(f"data/guilds/{guild.id}.json", "r") as f:
        data = json.load(f)
    targetDict = getUser(guild, linkedTo)
    for i, d in enumerate(data["users"]):
        if d == targetDict:
            data["users"].remove(d)
            break
    with open(f"data/guilds/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"- Removed user {targetDict['username']} (linked to {linkedTo}) from users in data/guilds/{guild.id}.json (connected to Server \"{guild.name}\")")

########### Commands ###########
# -------- /register -----------
@tree.command(
    name="register",
    description="Register yourself to play!"
)
async def register_command(ctx, username:str=None):
    await ctx.response.defer()

    await registerServer(ctx.guild)
    
    if(username==None):
        username=ctx.user.display_name

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

# ---------- /mine --------------
@tree.command(
    name="mine",
    description="Mine to get Items"
)
async def mine_command(ctx):
    await registerServer(ctx.guild)

    item = {
        "name": "testItem"
    }

    addItem(ctx.guild, ctx.user.id, item)

    await ctx.response.send_message("Complete!")

########### on_ready ###########
@client.event
async def on_ready():
    logger.info("Syncing Tree...")
    await tree.sync()
    logger.info("Ready!")

client.run(token, log_handler=None)
