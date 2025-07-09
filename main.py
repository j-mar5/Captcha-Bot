import discord
import os
import sys
import json
from discord.ext import commands
from Tools.utils import getGuildPrefix
from Tools.translate import Translate
from loguru import logger


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(getGuildPrefix, intents = intents)

# HELP
bot.remove_command("help") # To create a personal help command 

# Translate
bot.translate = Translate()



# Load cogs
# if __name__ == '__main__':
@bot.event
async def setup_hook():
    for filename in os.listdir("Cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"Cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info("Synced commands")
    logger.success(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name =f"for /help"))

# ------------------------ RUN ------------------------ # 
with open("config.json", "r") as config:
    data = json.load(config)
    token = data["token"]
    # Logger
    logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{" \
                "name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{" \
                "message}</level> "
    logger.remove()
    logger.add(sys.stdout, format=logger_format, level="DEBUG" if data["debug"] else "SUCCESS", enqueue=True, colorize=True)
bot.run(token) 