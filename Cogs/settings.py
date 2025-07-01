import discord
from Tools.utils import getConfig, getGuildPrefix
from discord.ext import commands
from discord import app_commands

# ------------------------ COGS ------------------------ #  

class SettingsCog(commands.Cog, name="settings command"):
    def __init__(self, bot):
        self.bot = bot
        

# ------------------------------------------------------ #  
    #Set command tree:
    #  config (config_group)
    #    ├── view (view)
    #    └── set (config_set_group)
    #        ├── captcha
    #        │   ├── enabled
    #        │   ├── verification_channel
    #        │   ├── verified_role
    #        │   ├── maintain_permissions
    #        │   ├── setup [pass in role & channel, or default to current hard-coded values]
    #        │   └── temp_role
    #        ├── language
    #        ├── log_channel
    #        └── min_account_age
    config_group = app_commands.Group(name="config", description="View and set configuration")
    config_set_group = app_commands.Group(name="set", description="Modify configuration", parent=config_group)

    @config_group.command(name = 'view',
                        description="Display the current configuration.")
    @app_commands.default_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def view (self, inter: discord.Interaction):

        data = getConfig(inter.guild_id)
        captcha = data["captcha"] 
        captchaChannel = data["captchaChannel"]  
        logChannel = data["logChannel"]
        temporaryRole = data["temporaryRole"]
        roleGivenAfterCaptcha = data["roleGivenAfterCaptcha"]
        minAccountAge = data["minAccountDate"]
        antispam = data["antiSpam"]
        allowSpam = data["allowSpam"]
        antiNudity = data["antiNudity"]
        antiProfanity =  data["antiProfanity"]
        language =  data["language"]
            
        minAccountAge = int(minAccountAge/3600)

        allowSpam2= ""
        if len(allowSpam) == 0:
            allowSpam2 = "None"
        else:
            for x in allowSpam:
                allowSpam2 = f"{allowSpam2}<#{x}>, "

        if roleGivenAfterCaptcha is not False:
            roleGivenAfterCaptcha = f"<@&{roleGivenAfterCaptcha}>"
        if captchaChannel is not False:
            captchaChannel = f"<#{captchaChannel}>"
        if logChannel is not False:
            logChannel = f"<#{logChannel}>"

        # prefix = await getGuildPrefix(self.bot, ctx)

        embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "settings", "SERVER_SETTINGS"), description=f"", color=0xdeaa0c)
        embed.add_field(name= self.bot.translate.msg(inter.guild_id, "settings", "CAPTCHA_PROTECTION").format("/"), value= self.bot.translate.msg(inter.guild_id, "settings", "CAPTCHA_PROTECTION_DESCRIPTION").format(captcha, captchaChannel, logChannel, temporaryRole), inline=False)
        embed.add_field(name= self.bot.translate.msg(inter.guild_id, "settings", "ROLE_GIVEN_AFTER_CAPTCHA").format("/"), value= self.bot.translate.msg(inter.guild_id, "settings", "ROLE_GIVEN_AFTER_CAPTCHA_DESCRIPTION").format(roleGivenAfterCaptcha), inline=False)
        embed.add_field(name= self.bot.translate.msg(inter.guild_id, "settings", "MINIMUM_ACCOUNT_AGE").format("/"), value= self.bot.translate.msg(inter.guild_id, "settings", "MINIMUM_ACCOUNT_AGE_DESCRIPTION").format(minAccountAge), inline=False)
        embed.set_footer(text=self.bot.translate.msg(inter.guild_id, "global", "BOT_CREATOR"))
        await inter.response.send_message(embed=embed)

    


# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))