import discord
from Tools.utils import getConfig, updateConfig
from discord.ext import commands
from discord import app_commands
import enum
# ------------------------ COGS ------------------------ # 
class Languages(str, enum.Enum):
    English = "en-US"
    French = "fr-FR"

class SettingsCog(commands.Cog, name="settings command"):
    def __init__(self, bot):
        self.bot = bot
        availableLanguage = [
            "en-US",
            "fr-FR"
        ]
        

# ------------------------------------------------------ #  
    #Set command tree:
    #  config (config_group)
    #    ├── view (view)
    #    └── set (config_set_group)
    #        ├── captcha (config_captcha_group)
    #        │   ├── enabled
    #        │   ├── verification_channel
    #        │   ├── verified_role
    #        │   ├── maintain_permissions
    #        │   ├── setup [pass in role & channel, or default to current hard-coded values]
    #        │   └── temp_role
    #        ├── language (language)
    #        ├── log_channel
    #        └── min_account_age
    config_group = app_commands.Group(name="config", description="View and set configuration", guild_only=True)
    config_set_group = app_commands.Group(name="set", description="Modify configuration", parent=config_group)
    config_captcha_group = app_commands.Group(name="captcha", description="Modify captcha configuration", parent=config_set_group)

    # /config view
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

        embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "settings", "SERVER_SETTINGS"), description=f"", color=0xdeaa0c)
        embed.add_field(name= self.bot.translate.msg(inter.guild_id, "settings", "CAPTCHA_PROTECTION").format("/"), value= self.bot.translate.msg(inter.guild_id, "settings", "CAPTCHA_PROTECTION_DESCRIPTION").format(captcha, captchaChannel, logChannel, temporaryRole), inline=False)
        embed.add_field(name= self.bot.translate.msg(inter.guild_id, "settings", "ROLE_GIVEN_AFTER_CAPTCHA").format("/"), value= self.bot.translate.msg(inter.guild_id, "settings", "ROLE_GIVEN_AFTER_CAPTCHA_DESCRIPTION").format(roleGivenAfterCaptcha), inline=False)
        embed.add_field(name= self.bot.translate.msg(inter.guild_id, "settings", "MINIMUM_ACCOUNT_AGE").format("/"), value= self.bot.translate.msg(inter.guild_id, "settings", "MINIMUM_ACCOUNT_AGE_DESCRIPTION").format(minAccountAge), inline=False)
        embed.set_footer(text=self.bot.translate.msg(inter.guild_id, "global", "BOT_CREATOR"))
        await inter.response.send_message(embed=embed)

    # /config set language
    @config_set_group.command(name="language", description="Set the bot's language")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def language(self, inter: discord.Interaction, language: Languages):
        # this is only used internally because I don't want to write a nasty one-liner to iterate the values of the enum above to fit in the structure of this translation method.
        # if adding support, ensure this is in sync with the enum above.
        availableLanguage = [
            "en-US",
            "fr-FR"
        ]
        if language not in Languages:
            await inter.response.send_message(self.bot.translate.msg(inter.guild_id, "changelanguage", "INVALID_LANGUAGE_SELECTED").format(str(availableLanguage)), ephemeral=True)
        
        data = getConfig(inter.guild_id)
        data["language"] = language
        updateConfig(inter.guild_id, data)
        
        await inter.response.send_message(self.bot.translate.msg(inter.guild_id, "changelanguage", "NEW_LANGUAGE").format(language))
    
    # /config set log channel
    @config_set_group.command(name="log channel", description="Set the channel to log bot events to (or disable this function if no channel is specified)")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def log_channel(self, inter: discord.Interaction, channel: discord.abc.GuildChannel):
        # Disable log if no channel specified
        if channel is None:
            # Read configuration.json
            data = getConfig(inter.guild_id)

            # Add modifications
            data["logChannel"] = False
            # Save
            updateConfig(inter.guild_id, data)
            # Respond
            embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_DISABLED"), 
                                  description = self.bot.translate.msg(ctx.guild.id, "logs", "LOG_CHANNEL_DISABLED_DESCRIPTION"), color = 0xe00000) # Red
            await inter.response.send_message(embed=embed)

        # Only allow text channels to be specified
        if not isinstance(channel, discord.TextChannel):
            embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_WRONG_TYPE"), 
                                  description=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_WRONG_TYPE_DESCRIPTION"), color=0xe00000) # Red
            await inter.response.send_message(embed=embed, ephemeral=True)
        # Verify we have permissions
        chan_perms = channel.overwrites_for(inter.guild.me)
        if not chan_perms.send_messages or not chan_perms.embed_links:
            # Try to fix them (if we have admin, for instance)
            try:
                chan_perms.send_messages = True
                chan_perms.embed_links = True
                await inter.channel.set_permissions(inter.guild.me, overwrite=chan_perms)
            # Forbidden - no access, must error out
            except discord.Forbidden:
                embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_MISSING_PERMISSIONS", 
                                                               description="LOG_CHANNEL_MISSING_PERMISSIONS_DESCRIPTION"))
                await inter.response.send_message(embed=embed, ephemeral=True)
        data = getConfig(inter.guild_id)
        # Add modifications
        data["logChannel"] = channel.id
        # Save
        updateConfig(inter.guild_id, data)
        # Respond
        embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_ENABLED"), 
                              description = self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_ENABLED_DESCRIPTION"), color = 0x2fa737) # Green
        

        

    


# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))