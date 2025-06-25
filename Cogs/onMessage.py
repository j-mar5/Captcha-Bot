import discord
import json
import aiohttp
from discord.ext import commands
from datetime import datetime
from io import BytesIO
from Tools.utils import getConfig
from Tools.logMessage import sendLogMessage

# ------------------------ COGS ------------------------ #  
class OnMessageCog(commands.Cog, name="on message"):
    def __init__(self, bot):
        self.bot = bot

# ------------------------------------------------------ #  

    @commands.Cog.listener()
    async def on_message(self, message):

        # If bot or Administrator
        if message.author.bot or message.author.guild_permissions.administrator is True:
            return

        if message.content == "" and len(message.attachments) == 0:
            return
               
        # Data
        data = getConfig(message.guild.id)
        antiProfanity =  data["antiProfanity"]
        antiSpam = data["antiSpam"] 
        allowSpam = data["allowSpam"]
        logChannel = data["logChannel"]


        # Anti spam
        if antiSpam is True:
            def check (message):
                return (message.author == message.author and (datetime.utcnow() - message.created_at).seconds < 15)

            if message.author.guild_permissions.administrator:
                return 

            if message.channel.id in allowSpam:
                return
                
            if len(list(filter(lambda m: check(m), self.bot.cached_messages))) >= 8 and len(list(filter(lambda m: check(m), self.bot.cached_messages))) < 12:
                await message.channel.send(self.bot.translate.msg(message.guild.id, "onMessage", "STOP_SPAM").format(message.author.mention))
            elif len(list(filter(lambda m: check(m), self.bot.cached_messages))) >= 12:
                embed = discord.Embed(title = self.bot.translate.msg(message.guild.id, "onMessage", "YOU_HAVE_BEEN_KICKED").format(message.author.guild.name), description =self.bot.translate.msg(message.guild.id, "onMessage", "YOU_HAVE_BEEN_KICKED_SPAM_REASON"), color = 0xff0000)
                await message.author.send(embed = embed)
                await message.author.kick() # Kick the user
                await message.channel.send(self.bot.translate.msg(message.guild.id, "onMessage", "USER_HAS_BEEN_KICKED_FOR_SPAMMING").format(message.author.mention))
                
                # Logs -> Create a hastbin file
                logTime = datetime.now().strftime("%m/%d/%Y at %H:%M:%S")
                logs = f"[LOGS] {self.bot.user.name.upper()} - ANTI-SPAM \n\n{message.author} ({message.author.id}) spammed in \"{message.channel}\" the {logTime}\n\n"
                messageNumber = 0

                # Get user messages
                user_cache_messages = [i for i in self.bot.cached_messages if i.author.id == message.author.id]
                
                for i in user_cache_messages[-10:]:
                    messageNumber += 1
                    logs = f"{logs}\n[{messageNumber}] {i.content}"

                url = 'https://hastebin.com'
                async with aiohttp.ClientSession() as session:
                    async with session.post(f'{url}/documents', data=logs) as hastbin:
                        hastbin = await hastbin.json()
                        hastbinUrl = url + "/" + hastbin['key']
                
                embed = discord.Embed(title = self.bot.translate.msg(message.guild.id, "onMessage", "MEMBER_HAS_BEEN_KICKED").format(message.author), description = self.bot.translate.msg(message.guild.id, "onMessage", "USER_HAS_BEEN_KICKED_FOR_SPAMMING_LOG").format(message.channel.mention, message.author, message.author.id, hastbinUrl), color = 0xff0000)
                await sendLogMessage(self, event=message, channel=logChannel, embed=embed)

# ------------------------ BOT ------------------------ #  

def setup(bot):
    bot.add_cog(OnMessageCog(bot))