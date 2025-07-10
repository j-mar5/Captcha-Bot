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
# Command tree:
# ├── config_view (config_view)
# ├── config_set (config_set_group)
# │   ├── language (language)
# │   ├── log_channel (log_channel)
# │   └── min_account_age TODO
# └── config_captcha (config_captcha_group)
#     ├── enabled (enabled)
#     ├── verification_channel TODO
#     ├── verified_role TODO
#     ├── maintain_permissions_on_new_channel TODO
#     ├── setup (setup)
#     ├── remove TODO
#     └── temp_role TODO
    
    config_set_group = app_commands.Group(name="config_set", description="Modify other bot configuration", guild_only=True)
    config_captcha_group = app_commands.Group(name="config_captcha", description="Modify captcha configuration",)

    # /config view
    @app_commands.command(name = 'config_view',
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
        language =  data["language"]
            
        minAccountAge = int(minAccountAge/3600)

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
        
    # /config_captcha enable
    @config_captcha_group.command(name="enable", description="Enables captcha protection. The protection must be fully setup (/config captcha setup) first.")
    async def enable(self, inter: discord.Interaction):
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
            if data["roleGivenAfterCaptcha"] != False:
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
    #/config_captcha disable
    @config_captcha_group.command(name="disable", description="Temporarily disables captcha protection.")
    async def disable(self, inter: discord.Interaction):
            # Read configuration.json
            data = getConfig(inter.guild_id)

            # Add modifications
            data["captcha"] = False
            # Save
            updateConfig(inter.guild_id, data)
            # Respond
            embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "SUCCESS"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "Captcha protection was deactivated successfully!"), color = 0x2fa737) # Green
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
        if data["captcha"] is True:
            embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                  description="Captcha protection is already set up! Disable the captcha first (/config captcha enabled).", color=0xe00000) # Red
            await inter.response.send_message(embed=embed)
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
                temporary_role: discord.PermissionOverwrite(read_messages = True, send_messages = True),
                inter.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages = True, embed_links = True, manage_messages = True) 
            }
            try:
                captchaChannel = await inter.guild.create_text_channel('verification', slowmode_delay=5, overwrites=overwrites)
            except discord.Forbidden as e:
                logger.warning(f"Failed to create verification channel: {e.text}")
                embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "TEMPORARY_CHANNEL_CREATE_ERROR_DESCRIPTION"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed)
            verification_channel = captchaChannel
            logger.info("...success!")
        # Verify we have permissions for the passed-in channel
        logger.info("Checking permissions for verification channel")
        chan_perms = verification_channel.overwrites_for(inter.guild.me)
        if not chan_perms.send_messages or not chan_perms.embed_links or not chan_perms.view_channel or not chan_perms.manage_messages:
            logger.debug("Found permissions issue, attempting to fix.")
            # Try to fix them (if we have admin, for instance)
            try:
                chan_perms.view_channel = True
                chan_perms.send_messages = True
                chan_perms.embed_links = True
                chan_perms.manage_messages = True
                await verification_channel.set_permissions(inter.guild.me, overwrite=chan_perms)
                logger.debug("...success!")
            # Forbidden - no access, must error out
            except discord.Forbidden:
                logger.warning("Failed to set permissions in the verification channel")
                embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                                               description=self.bot.translate.msg(inter.guild_id, "setup", "TEMPORARY_CHANNEL_SELECT_ERROR_DESCRIPTION"))
                return await inter.response.send_message(embed=embed, ephemeral=True)
        logger.info("...no issues found!")
        if log_channel is None:
             # Create log channel
            logger.info('Creating log channel and applying permissions')
            log_overwrites = {
                inter.guild.default_role: discord.PermissionOverwrite(read_messages = False),
                inter.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages = True, embed_links = True) 
            }
            try:
                logChannel = await inter.guild.create_text_channel('captcha-logs', overwrites=log_overwrites)
            except discord.Forbidden as e:
                logger.warning(f"Failed to create log channel: {e.text}")
                embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                  description = self.bot.translate.msg(inter.guild_id, "setup", "TEMPORARY_CHANNEL_CREATE_ERROR_DESCRIPTION"), color=0xe00000) # Red
                return await inter.response.send_message(embed=embed)
            log_channel = logChannel
            logger.info("...success!")
        # Verify we have permissions for the passed-in channel
        chan_perms = log_channel.overwrites_for(inter.guild.me)
        logger.info("Checking permissions for log channel")
        if not chan_perms.send_messages or not chan_perms.embed_links or not chan_perms.view_channel:
            logger.debug("Found permissions issue, attempting to fix")
            # Try to fix them (if we have admin, for instance)
            try:
                chan_perms.view_channel = True
                chan_perms.send_messages = True
                chan_perms.embed_links = True
                await verification_channel.set_permissions(inter.guild.me, overwrite=chan_perms)
            # Forbidden - no access, must error out
            except discord.Forbidden:
                logger.warning("Failed to set permissions in the verification channel")
                embed = discord.Embed(title=self.bot.translate.msg(inter.guild_id, "global", "ERROR"), 
                                                               description=self.bot.translate.msg(inter.guild_id, "setup", "LOG_CHANNEL_SELECT_ERROR_DESCRIPTION"))
                return await inter.response.send_message(embed=embed, ephemeral=True)
        # by this point both verification_channel and temporary_role should be valid objects of the Role and TextChannel types
        logger.info('Hiding all channels from the temporary role')
        await inter.response.defer()
        missedChannels = []


        for channel in inter.guild.channels:
            #skip the channels we just made as their permissions should already be set correctly
            if channel.id == verification_channel.id or channel.id == log_channel.id:
                logger.debug(f"Skipping {channel} since its ID matches one of the channels we just created")
                continue
            try:
                logger.debug(f'Starting to override the permissions for {channel}.')
                await channel.set_permissions(temporary_role, overwrite=discord.PermissionOverwrite(read_messages = False))
            except discord.Forbidden:
                logger.info(f"Failed to change permissions (likely missing access to channel {channel} ({channel.id}))")
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

        embed = discord.Embed(title = self.bot.translate.msg(inter.guild_id, "setup", "CAPTCHA_WAS_SET_UP_WITH_SUCCESS"), description = self.bot.translate.msg(inter.guild_id, "setup", "CAPTCHA_WAS_SET_UP_WITH_SUCCESS_DESCRIPTION"), color = 0x2fa737) # Green
        await inter.edit_original_response(embed=embed)

# ------------------------ BOT ------------------------ #  

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))