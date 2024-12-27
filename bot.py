from os import environ
import json
import logging
import logging.handlers
import random
import discord
from discord import app_commands, Embed
from discord.ui import View, Button
from dotenv import load_dotenv

"""
TODO LIST:
  * TODO add /sell with optional item
  * TODO add /info for item info
  * TODO add /inv and /inventory to view inventory
  * TODO add desctiptions to commands in /help
  * TODO add desctiptions to general in /help
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
if not load_dotenv():
    logger.warning("dotenv presumably empty")
token = environ.get('DISCORD_TOKEN')
if token == "":
    logger.critical("Could not load discord token")
    exit()

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

    logger.info(f"# Added server {guild.id} ({guild.name}) to data directory. PATH: data/guilds/{guild.id}.json")

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

# --- delete user from json ----
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

# --- add item to inventory ----
def addItem(guild:discord.Guild, linkedTo:int, item:dict):
    with open(f"data/guilds/{guild.id}.json", "r") as f:
        data = json.load(f)
    data["users"][getUser(guild=guild,linkedTo=linkedTo, getPos=True)]["inventory"].append(item)
    with open(f"data/guilds/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)

# - remove item from inventory -
def removeItem(guild:discord.Guild, linkedTo:int, item:str|dict):
    with open(f"data/guilds/{guild.id}.json", "r") as f:
        data = json.load(f)
    inv = getUser(guild=guild, linkedTo=linkedTo)["inventory"]
    userPos = getUser(guild=guild, linkedTo=linkedTo, getPos=True)
    if(type(item) == str):
        for i, dict in enumerate(inv):
            if dict["name"] == item:
                data["users"][userPos]["inventory"].remove(dict)
                break
    else:
        data["users"][userPos]["inventory"].remove(item)
    with open(f"data/guilds/{guild.id}.json", "w") as f:
        json.dump(data, f, indent=4)

# ----- get user from json -----
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

# -- get item from items.json --
def getItem(category:str, name:str, getPos:bool=False):
    with open("data/items.json") as f:
        data = json.load(f)
    for i in range(len(data[category])):
        item = data[category][i]
        if(item["name"] == name or item == name):
            if(getPos):
                return i
            return item
    return None

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
    await ctx.response.defer()

    await registerServer(ctx.guild)

    # check if user has Account
    if(getUser(ctx.guild, ctx.user.id) != None):
        # ~~~ PICK ITEM ~~~
        # pick random category from items.json
        with open("data/items.json") as f:
            items = json.load(f)
        itemCategory = items[random.choices(list(items), weights=[0.67, 0.33], k=1)[0]]

        # find weights of elements
        weights = [weight["rarity"]/100 for weight in itemCategory]

        # choose a random item with weights
        itemDict = random.choices(itemCategory, weights=weights, k=1)[0]

        # make itemName the name of the item in the .json
        itemName = itemDict["name"]

        # ~~~ QUANTITY ~~~
        # get inv
        inv = getUser(ctx.guild, ctx.user.id)["inventory"]

        # add 1 to the quantity if item is existent and remove old item
        quantity = 1
        for item in inv:
            if item["name"] == itemName:
                quantity = item["quantity"] + 1
                removeItem(ctx.guild, ctx.user.id, item)
                break

        # ~~~ ITEM DICT ~~~
        # create item dict
        item = {
            "name": itemName,
            "quantity": quantity
        }

        # add item to inv
        addItem(ctx.guild, ctx.user.id, item)

        embed = Embed(
            title="/mine",
            description=f"{getUser(ctx.guild, ctx.user.id)['username']} has just mined a {item['name']}!"
        )
    else:
        embed = Embed(
            title="/mine",
            description="You can't use /mine if you don't have an account",
            color=0xff0000
        )

    await ctx.followup.send(embed=embed)

# ---------- /help --------------
@tree.command(
    name="help",
    description="Need any help?"
)
@app_commands.describe(
    general="General help",
    commands="Help with Commands"
)
@app_commands.choices(
    general=[
        app_commands.Choice(name="Gameplay", value="gameplay")
    ],
    commands=[
        app_commands.Choice(name="Command list", value="list"),
        app_commands.Choice(name="/register", value="register"),
        app_commands.Choice(name="/del_account", value="del_account"),
        app_commands.Choice(name="/mine", value="mine")
    ]
)
async def help_command(ctx, 
    general:app_commands.Choice[str]=None, 
    commands:app_commands.Choice[str]=None
):
    await ctx.response.defer(ephemeral=True)

    await registerServer(ctx.guild)

    if general != None:
        match general.value:
            case "gameplay":
                embed = Embed(
                    title="/help general Gameplay",
                    description="Use /mine to mine"
                )

        await ctx.followup.send(embed=embed)
    elif commands != None:
        match commands.value:
            case "list":
                embed = Embed(
                    title="/help command list",
                    description=
                    "- /register\n"
                    "  - username\n"
                    "- /del_account\n"
                    "- /mine"
                )
            case "register":
                embed = Embed(
                    title="/help commands /register",
                    description=
                    "Use /register to register yourself on this server. "
                    "You can enter a username if you want a custom one. "
                    "If you don't enter a custom username it will automatically be set to your discord name. "
                )
            case "del_account":
                embed = Embed(
                    title="/help commands /del_account",
                    description=
                    "/del_account will delete your entire account on this server. "
                    "*Be careful*: This is *not* reversible. "
                    "When you enter the command you will have the option to cancel the deletation by pressing \"No\". "
                    "The \"Yes\" Button will *confirm* the deletation. "
                )
            case "mine":
                embed = Embed(
                    title="/help commands /mine",
                    description=
                    "Use /mine to mine a random item"
                )
        await ctx.followup.send(embed=embed)
    else:
        embed = Embed(
            title="/help",
            description="A basic Step by Step guide to get you started."
        )
        embed.add_field(
            name="1. Register Yourself",
            value=
            "To get started you first need to register. "
            "Type /register and give yourself a username if you want. "
            "If you don't enter a username it will automatically be set to your discord name.\n"
            "*Congratulations!* :tada:\n"
            "You have successfully registered!"
        )
        await ctx.followup.send(embed=embed)

########### on_ready ###########
@client.event
async def on_ready():
    logger.info("Syncing Tree...")
    await tree.sync()
    logger.info("Ready!")

client.run(token, log_handler=None)
