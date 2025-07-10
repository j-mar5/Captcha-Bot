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
from discord import app_commands
from discord.utils import get
from PIL import ImageFont, ImageDraw, Image
from Tools.utils import getConfig
import Tools.captchaUtils as captchaUtils
from Tools.logMessage import sendLogMessage
from loguru import logger

# ------------------------ COGS ------------------------ #  

class ReVerifyCog(commands.Cog, name="re-verify"):
    def __init__(self, bot):
        self.bot = bot

# ------------------------------------------------------ #  
    @app_commands.command(name="reverify", 
                          description="Marks a member for re-verification against the captcha.")
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def reverify(self, interaction: discord.Interaction, member: discord.Member):
        
        if (member.bot):
           return await interaction.response.send_message(content="Can't verify a bot!", ephemeral=True)
            

        # Read configuration.json
        data = getConfig(member.guild.id)
        if data["captcha"] is False:
            return await interaction.response.send_message(content="Captcha protection is disabled. Please enable it before reverifying a member.", ephemeral=True)
        logChannel = data["logChannel"]
        captchaChannel = self.bot.get_channel(data["captchaChannel"])

        memberTime = f"{member.joined_at.year}-{member.joined_at.month:02d}-{member.joined_at.day:02d} {member.joined_at.hour:02d}:{member.joined_at.minute:02d}:{member.joined_at.second:02d}"

        if data["captcha"] is True:
            logger.info(f"User {member} marked for re-verification")
            # Give temporary role
            logger.info("Giving new member the unverified role")
            getrole = get(member.guild.roles, id = data["temporaryRole"])
            await member.add_roles(getrole)
            await interaction.response.send_message(content=f"Prompted {member.display_name} ({member.global_name}) for a re-captcha!")

            # 5 chances to verify correctly
            remaining_attempts = 5
            while 1 > 0:
                logger.debug("Start reverify loop")
                # Generate a captcha

                numbers = '23456789' # restricted choices to avoid ambiguous characters
                letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ' # restricted choices to avoid ambiguous characters
                text = ' '.join(random.choice(numbers + letters) for _ in range(6)) # + string.ascii_lowercase + string.digits
                captchaFile = await captchaUtils.generateCaptcha(member, text)
                captchaEmbed = await captchaChannel.send(self.bot.translate.msg(member.guild.id, "reVerify", "REVERIFICATION_MESSAGE").format(member.mention), file= captchaFile)
                # Remove captcha folder
                logger.debug("...success! Removing image files on disk")
                try:
                    await captchaUtils.cleanup(member)
                except Exception as error:
                    logger.error(f"Delete captcha file failed {error}")

                # Wait 24 hours for a response from the user, verify() returns an enum of SUCCESS, FAIL, or TIMEOUT
                logger.debug(f"Calling verify in reverify for {member}, timeout 24 hours.")
                result = await captchaUtils.verify(self=self, member=member, text=text, timeout=86400)
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
                    logger.info("Stopping reverify loop on successful captcha")
                    return

                elif result == captchaUtils.ReturnStatus.FAIL:
                    logger.debug(f"Received failure in checking {member}. remaining_attempts is at {remaining_attempts}")
                    # kick if all attempts have been used
                    if remaining_attempts == 1:
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
                        logger.info("Stopping reverify loop on a kick for excessive failures")
                        # do not continue the loop
                        return
                    else:
                        # notify of failure, decrement attempts remaining and continue the loop
                        remaining_attempts -= 1
                        logger.debug(f"Decremented remaining_attempts, now {remaining_attempts}")
                        embed = discord.Embed(description=self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA").format(member.mention, remaining_attempts), color=0xca1616) # Red
                        await captchaChannel.send(embed = embed, delete_after = 5)
                        time.sleep(3)
                        try:
                            await captchaEmbed.delete()
                        except (discord.errors.NotFound, discord.Forbidden):
                            logger.error("Delete message in verification channel failed, check permissions")
                            pass
                elif result == captchaUtils.ReturnStatus.TIMEOUT:
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
                    # do not continue the loop
                    logger.info("Stopping reverify loop on a kick for verification timeout")
                    return

# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(ReVerifyCog(bot))