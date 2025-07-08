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
from Tools.captchaUtils import generateCaptcha, cleanup
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
    async def reverify(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if (member.bot):
            await interaction.edit_original_response(content="Can't verify a bot!")
            return

        # Read configuration.json
        data = getConfig(member.guild.id)
        logChannel = data["logChannel"]
        captchaChannel = self.bot.get_channel(data["captchaChannel"])

        memberTime = f"{member.joined_at.year}-{member.joined_at.month:02d}-{member.joined_at.day:02d} {member.joined_at.hour:02d}:{member.joined_at.minute:02d}:{member.joined_at.second:02d}"

        if data["captcha"] is True:
            logger.info(f"User {member} marked for re-verification, starting captcha generation")
            # Give temporary role
            logger.info("Giving new member the unverified role")
            getrole = get(member.guild.roles, id = data["temporaryRole"])
            await member.add_roles(getrole)

            # Generate captcha
            numbers = '23456789' # restricted choices to avoid ambiguous characters
            letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ' # restricted choices to avoid ambiguous characters
            text = ' '.join(random.choice(numbers + letters) for _ in range(6)) # + string.ascii_lowercase + string.digits
            captchaFile = await generateCaptcha(member, text)
            # Send message and cleanup captcha files
            captchaEmbed = await captchaChannel.send(self.bot.translate.msg(member.guild.id, "reVerify", "REVERIFICATION_MESSAGE").format(member.mention), file= captchaFile)
            await cleanup(member)
            await interaction.edit_original_response(content=f"Prompted {member.display_name} ({member.global_name}) for a re-captcha!")

            # Check if it is the right user
            # TODO: need to delete messages if not
            def check(message):
                if message.author == member and  message.content != "":
                    return message.content

            try:
                logger.info(f"Starting timer for {member}")
                msg = await self.bot.wait_for('message', timeout=86400.0, check=check)
                logger.info(f"Message received from {member}, checking captcha")
                # Check the captcha
                password = text.split(" ")
                password = "".join(password)
                if msg.content == password:
                    logger.debug("...password correct!")
                    embed = discord.Embed(description=self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_PASSED_THE_CAPTCHA").format(member.mention), color=0x2fa737) # Green
                    await captchaChannel.send(embed = embed, delete_after = 5)
                    # Give and remove roles
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
                    time.sleep(3)
                    try:
                        await captchaEmbed.delete()
                    except discord.errors.NotFound:
                        pass
                    try:
                        await msg.delete()
                    except discord.errors.NotFound:
                        pass
                    # Logs
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_PASSED_THE_CAPTCHA").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "USER_INFORMATIONS").format(member, member.id), color = 0x2fa737)
                    embed.set_footer(text= self.bot.translate.msg(member.guild.id, "onJoin", "DATE").format(memberTime))
                    await sendLogMessage(self, event=member, channel=logChannel, embed=embed)

                else:
                    embed = discord.Embed(description=self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA").format(member.mention), color=0xca1616) # Red
                    await captchaChannel.send(embed = embed, delete_after = 5)
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "YOU_HAVE_BEEN_KICKED").format(member.guild.name), description = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA_REASON"), color = 0xff0000)

                    try:
                        await member.send(embed=embed)
                    except discord.errors.Forbidden:
                        # can't send dm to user
                        pass
                    try:
                        await member.kick()
                    except discord.Forbidden:
                        embed = discord.Embed(title=self.bot.translate.msg(member.guild.id, "global", "ERROR"), 
                                              description=f"Missing permissions to kick a member who failed the captcha: {member.display_name} ({member.id})")
                        await sendLogMessage(self, event=member, channel=logChannel, embed=embed)

                    time.sleep(3)
                    try:
                        await captchaEmbed.delete()
                    except discord.errors.NotFound:
                        pass
                    try:
                        await msg.delete()
                    except discord.errors.NotFound:
                        pass
                    # Logs
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_HAS_BEEN_KICKED").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_FAILED_THE_CAPTCHA_REASON_LOG").format(member, member.id), color = 0xff0000)
                    embed.set_footer(text= self.bot.translate.msg(member.guild.id, "onJoin", "DATE").format(memberTime))
                    await sendLogMessage(self, event=member, channel=logChannel, embed=embed)

            except (asyncio.TimeoutError):
                embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "TIME_IS_OUT"), description = self.bot.translate.msg(member.guild.id, "onJoin", "REVERIFY_USER_HAS_EXCEEDED_THE_RESPONSE_TIME").format(member.mention), color = 0xff0000)
                await captchaChannel.send(embed = embed, delete_after = 5)
                try:
                    embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "YOU_HAVE_BEEN_KICKED").format(member.guild.name), description = self.bot.translate.msg(member.guild.id, "onJoin", "REVERIFY_USER_HAS_EXCEEDED_THE_RESPONSE_TIME_REASON"), color = 0xff0000)
                    await member.send(embed = embed)
                    await member.kick() # Kick the user
                except Exception as error:
                    print(f"Log failed (onJoin) : {error}")
                time.sleep(3)
                await captchaEmbed.delete()
                # Logs
                embed = discord.Embed(title = self.bot.translate.msg(member.guild.id, "onJoin", "MEMBER_HAS_BEEN_KICKED").format(member), description = self.bot.translate.msg(member.guild.id, "onJoin", "REVERIFY_USER_HAS_EXCEEDED_THE_RESPONSE_TIME_LOG").format(member, member.id), color = 0xff0000)
                embed.set_footer(text= self.bot.translate.msg(member.guild.id, "onJoin", "DATE").format(memberTime))
                await sendLogMessage(self, event=member, channel=logChannel, embed=embed)

# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(ReVerifyCog(bot))