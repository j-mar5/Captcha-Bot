import discord
import numpy as np
import random
import string
import Augmentor
import os
import shutil
import asyncio
import time
from discord.ext import commands
from discord.utils import get
from PIL import ImageFont, ImageDraw, Image
import Tools.captchaUtils as captchaUtils
from Tools.utils import getConfig
from Tools.logMessage import sendLogMessage
from loguru import logger

# ------------------------ COGS ------------------------ #  

class OnJoinCog(commands.Cog, name="on join"):
    def __init__(self, bot):
        self.bot = bot

# ------------------------------------------------------ #  

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if (member.bot):
            return

        # Read configuration.json
        data = getConfig(member.guild.id)
        logChannel = data["logChannel"]
        captchaChannel = self.bot.get_channel(data["captchaChannel"])

        memberTime = f"{member.joined_at.year}-{member.joined_at.month}-{member.joined_at.day} {member.joined_at.hour}:{member.joined_at.minute}:{member.joined_at.second}"

        # Check the user account creation date (1 day by default)
        if data["minAccountDate"] is False:
            userAccountDate = member.created_at.timestamp()
            if userAccountDate < data["minAccountDate"]:
                minAccountDate = data["minAccountDate"] / 3600
                embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "YOU_HAVE_BEEN_KICKED").format(member.guild.name), description = self.bot.translate.msg(member.guild.id, "onJoin", "MIN_ACCOUNT_AGE_KICK_REASON").format(minAccountDate), color = 0xff0000)
                await member.send(embed = embed)
                await member.kick() # Kick the user
                # Logs
                embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "HAS_BEEN_KICKED").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "MIN_ACCOUNT_AGE_HAS_BEEN_KICKED_REASON").format(minAccountDate, member.created_at, member, member.id), color = 0xff0000)
                embed.set_footer(text= f"at {member.joined_at}")
                await sendLogMessage(self, event=member, channel=logChannel, embed=embed)

        if data["captcha"] is True:
            logger.info(f"User {member} joined, starting captcha")
            # Give temporary role
            logger.info("Giving new member the unverified role")
            getrole = get(member.guild.roles, id = data["temporaryRole"])
            await member.add_roles(getrole)
            
            

            # Check if it is the right user
            # TODO: need to delete messages if not
            # def check(message):
            #     if message.author == member and  message.content != "":
            #         return message.content

            # try:
                # logger.info(f"Starting timer for {member}")
                # msg = await self.bot.wait_for('message', timeout=300.0, check=check)
                # logger.info(f"Message received from {member}, checking captcha")
                # # Check the captcha
                # password = text.split(" ")
                # password = "".join(password)
                # if msg.content == password:

            # 3 chances to guess correctly
            remaining_attempts = 3
            while remaining_attempts > 0:
                # Generate a captcha

                numbers = '23456789' # restricted choices to avoid ambiguous characters
                letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ' # restricted choices to avoid ambiguous characters
                text = ' '.join(random.choice(numbers + letters) for _ in range(6)) # + string.ascii_lowercase + string.digits
                captchaFile = await captchaUtils.generateCaptcha(member, text)
                captchaEmbed = await captchaChannel.send(self.bot.translate.msg(member.guild.id, "onJoin", "CAPTCHA_MESSAGE").format(member.mention), file= captchaFile)
                # Remove captcha folder
                logger.debug("...success! Removing image files on disk")
                try:
                    await captchaUtils.cleanup(member)
                except Exception as error:
                    logger.error(f"Delete captcha file failed {error}")

                # Wait 5 minutes for a response from the user, verify() returns an enum of SUCCESS, FAIL, or TIMEOUT
                result = await captchaUtils.verify(self=self, member=member, text=text, timeout=300)
                if result == captchaUtils.ReturnStatus.SUCCESS:
                    embed = discord.Embed(description=self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_PASSED_THE_CAPTCHA").format(member.mention), color=0x2fa737) # Green
                    await captchaChannel.send(embed = embed, delete_after = 5)
                    # Give and remove roles as configured
                    try:
                        getrole = get(member.guild.roles, id = data["roleGivenAfterCaptcha"])
                        if getrole is not False:
                            await member.add_roles(getrole)
                    except Exception as error:
                        logger.warning(f"Give and remove roles failed for {member}: {error}")
                    try:
                        getrole = get(member.guild.roles, id = data["temporaryRole"])
                        await member.remove_roles(getrole)
                    except Exception as error:
                        logger.warning(f"No temp role found to remove from {member}: {error}")
                    # Delete captcha post
                    time.sleep(3)
                    try:
                        await captchaEmbed.delete()
                    except discord.errors.NotFound:
                        pass
                
                    # Logs
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_PASSED_THE_CAPTCHA").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "USER_INFORMATIONS").format(member, member.id), color = 0x2fa737)
                    embed.set_footer(text= self.bot.translate.msg(member.guild.id, "onJoin", "DATE").format(memberTime))
                    await sendLogMessage(self, event=member, channel=logChannel, embed=embed)
                    # do not continue the loop
                    return

                elif result == captchaUtils.ReturnStatus.FAIL:
                    # kick if all attempts have been used
                    if remaining_attempts == 0:
                        embed = discord.Embed(description=self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA").format(member.mention, remaining_attempts), color=0xca1616) # Red
                        await captchaChannel.send(embed = embed, delete_after = 5)
                        embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "YOU_HAVE_BEEN_KICKED").format(member.guild.name), description = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA_REASON"), color = 0xff0000)

                        try:
                            await member.send(embed=embed)
                        except discord.errors.Forbidden:
                            # can't send dm to user
                            pass
                        await member.kick()
                        embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_HAS_BEEN_KICKED").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA_REASON_LOG").format(member, member.id), color = 0xff0000)
                        embed.set_footer(text= self.bot.translate.msg(member.guild.id, "onJoin", "DATE").format(memberTime))
                        await sendLogMessage(self, event=member, channel=logChannel, embed=embed)
                        #delete captcha post
                        time.sleep(3)
                        try:
                            await captchaEmbed.delete()
                        except (discord.errors.NotFound, discord.Forbidden):
                            logger.error("Delete message in verification channel failed, check permissions")
                            pass
                        # do not continue the loop
                        return
                    else:
                        # notify of failure, decrement attempts remaining and continue the loop
                        embed = discord.Embed(description=self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA").format(member.mention, remaining_attempts), color=0xca1616) # Red
                        await captchaChannel.send(embed = embed, delete_after = 5)
                        remaining_attempts -= 1
                        time.sleep(3)
                        try:
                            await captchaEmbed.delete()
                        except (discord.errors.NotFound, discord.Forbidden):
                            logger.error("Delete message in verification channel failed, check permissions")
                            pass
                elif result == captchaUtils.ReturnStatus.TIMEOUT:
            # except (asyncio.TimeoutError):
                    # immediately kick, likely a bot user
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "TIME_IS_OUT"), description = self.bot.translate.msg(member.guild.id, "onJoin", "USER_HAS_EXCEEDED_THE_RESPONSE_TIME").format(member.mention), color = 0xff0000)
                    await captchaChannel.send(embed = embed, delete_after = 5)
                    try:
                        embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "YOU_HAVE_BEEN_KICKED").format(member.guild.name), description = self.bot.translate.msg(member.guild.id, "onJoin", "USER_HAS_EXCEEDED_THE_RESPONSE_TIME_REASON"), color = 0xff0000)
                        await member.send(embed = embed)
                        await member.kick() # Kick the user
                    except Exception as error:
                        print(f"Log failed (onJoin) : {error}")
                    time.sleep(3)
                    await captchaEmbed.delete()
                    # Logs
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_HAS_BEEN_KICKED").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "USER_HAS_EXCEEDED_THE_RESPONSE_TIME_LOG").format(member, member.id), color = 0xff0000)
                    embed.set_footer(text= self.bot.translate.msg(member.guild.id, "onJoin", "DATE").format(memberTime))
                    await sendLogMessage(self, event=member, channel=logChannel, embed=embed)

# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(OnJoinCog(bot))