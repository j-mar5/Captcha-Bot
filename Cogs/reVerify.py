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
            
            logger.info("Generating captcha")
            logger.debug("Creating background of captcha")
            # Create captcha
            image = np.zeros(shape= (100, 350, 3), dtype= np.uint8)

            # Create image 
            image = Image.fromarray(image+255) # +255 : black to white
            logger.debug("...success! Adding random text")
            # Add text
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(font= "Tools/arial.ttf", size= 60)

            numbers = '23456789' # restricted choices to avoid ambiguous characters
            letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ' # restricted choices to avoid ambiguous characters
            text = ' '.join(random.choice(numbers + letters) for _ in range(6)) # + string.ascii_lowercase + string.digits
    
            # Center the text
            W, H = (350,100)
            w = draw.textlength(text, font= font)
            h = 45 # magic constant to vertically center the captcha characters in a 100-px space
            draw.text(((W-w)/2,(H-h)/2), text, font= font, fill= (90, 90, 90))

            # Save
            logger.debug("...success! Saving temporary image to disk")
            ID = member.id
            folderPath = f"captchaFolder/{member.guild.id}/captcha_{ID}"
            try:
                os.mkdir(folderPath)
            except:
                if os.path.isdir(f"captchaFolder/{member.guild.id}") is False:
                    os.mkdir(f"captchaFolder/{member.guild.id}")
                if os.path.isdir(folderPath) is True:
                    shutil.rmtree(folderPath)
                os.mkdir(folderPath)
            image.save(f"{folderPath}/captcha{ID}.png")

            # Deform
            logger.debug("...success! Deforming image")
            p = Augmentor.Pipeline(folderPath)
            p.random_distortion(probability=1, grid_width=2, grid_height=2, magnitude=35)
            p.process()

            # Search file in folder
            path = f"{folderPath}/output"
            files = os.listdir(path)
            captchaName = [i for i in files if i.endswith('.png')]
            captchaName = captchaName[0]

            image = Image.open(f"{folderPath}/output/{captchaName}")
            
            # Add line
            width = random.randrange(10, 15)
            co1 = random.randrange(0, 75)
            co3 = random.randrange(275, 350)
            co2 = random.randrange(20, 50)
            co4 = random.randrange(20, 50)
            draw = ImageDraw.Draw(image)
            draw.line([(co1, co2), (co3, co4)], width= width, fill= (90, 90, 90))

            # Add another
            width = random.randrange(12, 15)
            co1 = random.randrange(0, 75)
            co3 = random.randrange(275, 350)
            co2 = random.randrange(60, 90)
            co4 = random.randrange(60, 90)
            draw = ImageDraw.Draw(image)
            draw.line([(co1, co2), (co3, co4)], width= width, fill= (90, 90, 90))
            
            # Add noise
            noisePercentage = 0.60 # 25%

            pixels = image.load() # create the pixel map
            for i in range(image.size[0]): # for every pixel:
                for j in range(image.size[1]):
                    rdn = random.random() # Give a random %
                    if rdn < noisePercentage:
                        pixels[i,j] = (90, 90, 90)

            # Save
            logger.debug("...success! Saving final captcha image to disk")
            image.save(f"{folderPath}/output/{captchaName}_2.png")

            # Send captcha
            logger.debug("...success! Sending captcha image to user")
            captchaFile = discord.File(f"{folderPath}/output/{captchaName}_2.png")
            captchaEmbed = await captchaChannel.send(self.bot.translate.msg(member.guild.id, "reVerify", "REVERIFICATION_MESSAGE").format(member.mention), file= captchaFile)
            # Remove captcha folder
            logger.debug("...success! Removing image files on disk")
            try:
                shutil.rmtree(folderPath)
            except Exception as error:
                logger.error(f"Delete captcha file failed {error}")
            await interaction.edit_original_response(content=f"Prompted {member.display_name} ({member.global_name}) for a re-captcha!")

            # Check if it is the right user
            def check(message):
                if message.author == member and  message.content != "":
                    return message.content

            try:
                logger.info(f"Starting timer for {member}")
                msg = await self.bot.wait_for('message', timeout=43200.0, check=check)
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
                    await member.kick()

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