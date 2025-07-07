import discord
from Tools.utils import getConfig, updateConfig
from discord.ext import commands
from discord import app_commands
import enum
from typing import Optional
from loguru import logger
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
    #config (config_group)
    #   ├── view (view)
    #   ├── set (config_set_group)
    #   │       ├── language (language)
    #   │       ├── log_channel
    #   │       └── min_account_age
    #   └── captcha (config_captcha_group)
    #       ├── enabled
    #       ├── verification_channel
    #       ├── verified_role
    #       ├── maintain_permissions_on_new_channel
    #       ├── setup [pass in role & channel, or default to current hard-coded values]
    #       └── temp_role
    config_group = app_commands.Group(name="config", description="View and set configuration", guild_only=True)
    config_set_group = app_commands.Group(name="set", description="Modify configuration", parent=config_group)
    config_captcha_group = app_commands.Group(name="captcha", description="Modify captcha configuration", parent=config_group)

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
    
    # /config set log_channel
    @config_set_group.command(name="log_channel", description="Set the channel to log bot events to (or disable this function if no channel is specified)")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def log_channel(self, inter: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        # Disable log if no channel specified
        if channel is None:
            # Read configuration.json
            data = getConfig(inter.guild_id)

            # Add modifications
            data["logChannel"] = False
            # Save
            updateConfig(inter.guild_id, data)
            # Respond
            embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "SUCCESS"), 
                                  description = self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_DISABLED_DESCRIPTION"), color = 0x2fa737) # Green
            return await inter.response.send_message(embed=embed)
            

        # Only allow text channels to be specified
        if not isinstance(channel, discord.TextChannel):
            embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_WRONG_TYPE"), 
                                  description=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_WRONG_TYPE_DESCRIPTION"), color=0xe00000) # Red
            return await inter.response.send_message(embed=embed, ephemeral=True)
        # Verify we have permissions
        chan_perms = channel.overwrites_for(inter.guild.me)
        if not chan_perms.send_messages or not chan_perms.embed_links or not chan_perms.view_channel:
            # Try to fix them (if we have admin, for instance)
            try:
                chan_perms.view_channel = True
                chan_perms.send_messages = True
                chan_perms.embed_links = True
                await channel.set_permissions(inter.guild.me, overwrite=chan_perms)
            # Forbidden - no access, must error out
            except discord.Forbidden:
                embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_MISSING_PERMISSIONS"), 
                                                               description=self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_MISSING_PERMISSIONS_DESCRIPTION"))
                return await inter.response.send_message(embed=embed, ephemeral=True)
        data = getConfig(inter.guild_id)
        # Add modifications
        data["logChannel"] = channel.id
        # Save
        updateConfig(inter.guild_id, data)
        # Respond
        embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "SUCCESS"), 
                              description = self.bot.translate.msg(inter.guild_id, "logs", "LOG_CHANNEL_ENABLED_DESCRIPTION"), color = 0x2fa737) # Green
        return await inter.response.send_message(embed=embed)
        
    # /config captcha enabled
    @config_captcha_group.command(name="enabled", description="Enables or disables captcha. The protection must be fully setup (/config captcha setup) first.")
    async def enabled(self, inter: discord.Interaction, enabled: bool):
        if not enabled:
            # Read configuration.json
            data = getConfig(inter.guild_id)

            # Add modifications
            data["captcha"] = False
            # Save
            updateConfig(inter.guild_id, data)
            # Respond
            embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "SUCCESS"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "CAPTCHA_WAS_DELETED_WITH_SUCCESS_DESCRIPTION"), color = 0x2fa737) # Green
            return await inter.response.send_message(embed=embed)
        else:
            # Check that all configuration parameters are set and valid (e.g. roles, channels) before setting captcha true
            # Read configuration.json
            data = getConfig(inter.guild_id)
            # Check channel exists
            configuredChannel = data["captchaChannel"]
            actualChannel = inter.guild.get_channel(configuredChannel)
            if actualChannel is None:
                embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "global", "ERROR"),
                                      description=self.bot.translate.msg(inter.guild_id, "settings", "SETUP_CHANNEL_CHECK_FAILURE"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed, ephemeral=True)
            # Check verification role exists
            configuredRole = data["temporaryRole"]
            actualRole = inter.guild.get_role(configuredRole)
            if actualRole is None:
                embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "global", "ERROR"),
                                      description=self.bot.translate.msg(inter.guild_id, "settings", "SETUP_ROLE_CHECK_FAILURE"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed, ephemeral=True)
            # If configured, check post-captcha role exists
            if data["roleGivenAfterCaptcha"] != "false":
                configuredRole = data["roleGivenAfterCaptcha"]
                actualRole = inter.guild.get_role(configuredRole)
                if actualRole is None:
                    embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "global", "ERROR"),
                                         description=self.bot.translate.msg(inter.guild_id, "settings", "SETUP_POST_ROLE_CHECK_FAILURE"), color=0xe00000) # Red
                    return await inter.response.send_message(embed=embed, ephemeral=True)
            # All checks pass, enable
            # Add modifications
            data["captcha"] = True
            # Save
            updateConfig(inter.guild_id, data)
            # Respond
            embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "SUCCESS"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "CAPTCHA_WAS_SET_UP_WITH_SUCCESS_DESCRIPTION"), color = 0x2fa737) # Green
            return await inter.response.send_message(embed=embed)




    @config_captcha_group.command(name="setup", description="Configures the captcha protection. Bot attempts to create empty parameters.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(verification_channel = "The channel used to send and receive CAPTCHA challenges. (Default: bot creates #verification)")
    @app_commands.describe(temporary_role = "The temporary role given to users upon join. (Default: bot creates \"untested\")")
    @app_commands.describe(role_after_captcha = "The role to give to users upon successful verification (optional)")
    @app_commands.describe(log_channel = "The channel to send log messages to. (Default: bot creates #captcha-logs)")
    async def setup(self, inter: discord.Interaction, verification_channel: Optional[discord.TextChannel] = None, temporary_role: Optional[discord.Role] = None, log_channel: Optional[discord.TextChannel] = None, role_after_captcha: Optional[discord.Role] = None):
        if isinstance(inter.channel, discord.ForumChannel) or isinstance(inter.channel, discord.CategoryChannel):
            await inter.response.send_message("This command can only be run from a text channel, please try again.")
        # Open guild configuration
        data = getConfig(inter.guild_id)
        if temporary_role is None:
            logger.info('Creating the temporary role to be applied to new users')
            try:
                temporaryRole = await inter.guild.create_role(name="untested")
            except discord.Forbidden:
                embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "TEMPORARY_ROLE_CREATE_ERROR_DESCRIPTION"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed)
            temporary_role = temporaryRole
            logger.info("...success!")
        if verification_channel is None:
             # Create captcha channel
            logger.info('Creating verification channel and applying permissions')
            overwrites = {
                inter.guild.default_role: discord.PermissionOverwrite(read_messages = False),
                temporary_role: discord.PermissionOverwrite(read_messages = True, send_messages = True) 
            }
            try:
                captchaChannel = await inter.guild.create_text_channel('verification', slowmode_delay=5, overwrites=overwrites)
            except discord.Forbidden:
                embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "TEMPORARY_CHANNEL_CREATE_ERROR_DESCRIPTION"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed)
            verification_channel = captchaChannel
            logger.info("...success!")
        if log_channel is None:
             # Create log channel
            logger.info('Creating log channel and applying permissions')
            try:
                logChannel = await inter.guild.create_text_channel('captcha-logs', overwrites={inter.guild.default_role: discord.PermissionOverwrite(read_messages = False)})
            except discord.Forbidden:
                embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "TEMPORARY_CHANNEL_CREATE_ERROR_DESCRIPTION"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed)
            log_channel = logChannel
            logger.info("...success!")
        # by this point both verification_channel and temporary_role should be valid objects of the Role and TextChannel types
        logger.info('Hiding all channels from the temporary role')
        await inter.response.defer()
        missedChannels = []


        for channel in inter.guild.channels:
            try:
                logger.debug(f'Starting to override the permissions for {channel}.')
                await channel.set_permissions(temporary_role, overwrite=discord.PermissionOverwrite(read_messages = False))
            except discord.Forbidden:
                logger.error(f"Failed to change permissions (likely missing access to channel {channel} ({channel.id}))")
                missedChannels.append(channel.name)
        if len(missedChannels) > 0:
            errors = ", ".join(missedChannels)
            embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "setup", "CHANNEL_ACCESS_WARNING"), description=self.bot.translate.msg(inter.guild_id, "setup", "CHANNEL_ACCESS_WARNING_DESCRIPTION").format(errors), color=0xffff00) # Yellow
            await inter.channel.send(embed=embed)

        # Edit configuration.json
        # Add modifications
        logger.debug('Saving data to configuration')
        data["captcha"] = True
        data["temporaryRole"] = temporary_role.id
        data["captchaChannel"] = verification_channel.id
        data["logChannel"] = log_channel.id
        if role_after_captcha != None:
            data["roleGivenAfterCaptcha"] = role_after_captcha.id
        updateConfig(inter.guild_id, data)
        logger.debug("...success!")

# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))