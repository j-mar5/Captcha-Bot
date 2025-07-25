import discord
import numpy as np
import random
import Augmentor
import os
import shutil
from PIL import ImageFont, ImageDraw, Image
from Tools.logMessage import sendLogMessage
from loguru import logger
import asyncio
import time
from enum import IntEnum

class ReturnStatus(IntEnum):
    SUCCESS = 0
    FAIL = 1
    TIMEOUT = 2


async def generateCaptcha(member: discord.Member, text: str):
    image = np.zeros(shape= (100, 350, 3), dtype= np.uint8)

    # Create image 
    image = Image.fromarray(image+255) # +255 : black to white
    logger.debug("...success! Adding random text")
    # Add text
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font= "Tools/arial.ttf", size= 60)

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
    noisePercentage = 0.60 # 60%

    pixels = image.load() # create the pixel map
    for i in range(image.size[0]): # for every pixel:
        for j in range(image.size[1]):
            rdn = random.random() # Give a random %
            if rdn < noisePercentage:
                pixels[i,j] = (90, 90, 90)

    # Save
    logger.debug("...success!")
    image.save(f"{folderPath}/output/{captchaName}_2.png")
    return discord.File(f"{folderPath}/output/{captchaName}_2.png")

async def cleanup(member: discord.Member):
    ID = member.id
    folderPath = f"captchaFolder/{member.guild.id}/captcha_{ID}"
    logger.debug("Removing image files on disk")
    try:
        shutil.rmtree(folderPath)
    except Exception as error:
        logger.error(f"Delete captcha file failed {error}")

async def verify(self, member, text: str, timeout: int):
    def check(message):
        if message.author == member and  message.content != "":
            return message.content
        
    try:
        logger.info(f"Starting timer for {member}")
        msg = await self.bot.wait_for('message', timeout=timeout, check=check)
        logger.info(f"Message received from {member}, checking captcha")
        # Check the captcha
        password = text.split(" ")
        password = "".join(password)
        if msg.content == password:
            logger.info("...password correct!")
            try:
                await msg.delete()
            except (discord.errors.NotFound, discord.Forbidden):
                logger.info("Delete message in verification channel failed, check permissions")
                pass
            return ReturnStatus.SUCCESS
        else:
            logger.info(f"...password incorrect! Got {msg.content}, expected {password}")
            try:
                await msg.delete()
            except (discord.errors.NotFound, discord.Forbidden):
                logger.info("Delete message in verification channel failed, check permissions")
                pass
            return ReturnStatus.FAIL
    except (asyncio.TimeoutError):
        logger.debug("...timed out!")
        return ReturnStatus.TIMEOUT