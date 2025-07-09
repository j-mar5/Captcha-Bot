import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

# ------------------------ COGS ------------------------ #  

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# ------------------------------------------------------ #  

    @app_commands.command(name="help", 
                          description="Show the help page.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages = True)
    async def help(self, inter: discord.Interaction, commandName: Optional[str] = None):

        commandName2 = None
        stop = False

        if commandName is not None:
            for i in self.bot.commands:
                if i.name == commandName.lower():
                    commandName2 = i
                    break 
                else:
                    for j in i.aliases:
                        if j == commandName.lower():
                            commandName2 = i
                            stop = True
                            break
                if stop:
                    break 

            if commandName2 is None:
                await inter.response.send_message("No command found!", ephemeral=True)   
            else:
                embed = discord.Embed(title=f"**{commandName2.name.upper()} COMMAND :**", description="", color=0xdeaa0c)
                embed.set_thumbnail(url=f'{str(self.bot.user.display_avatar)}')
                embed.add_field(name=f"**NAME :**", value=f"{commandName2.name}", inline=False)
                aliases = ""
                if len(commandName2.aliases) > 0:
                    for aliase in commandName2.aliases:
                        aliases = aliase
                else:
                    commandName2.aliases = None
                    aliases = None
                embed.add_field(name=f"**ALIASES :**", value=f"{aliases}", inline=False)
                if commandName2.usage is None:
                    commandName2.usage = ""
                    
                
                embed.add_field(name=f"**USAGE :**", value=f"/{commandName2.name} {commandName2.usage}", inline=False)
                embed.add_field(name=f"**DESCRIPTION :**", value=f"{commandName2.description}", inline=False)
                embed.set_footer(text="Captcha Bot")
                await inter.response.send_message(embed=embed)
        else:

            embed = discord.Embed(title=f"__**Help page of {self.bot.user.name.upper()}**__", description="**/help (command) :**Display the help list or the help data for a specific command.", color=0xdeaa0c)
            embed.set_thumbnail(url=f'{str(self.bot.user.display_avatar)}')
            embed.add_field(name=f"__ADMIN :__", value=f"**/config_captcha setup [#verification-channel] [@verification_role] [#log_channel] [@role_after_captcha]:** Set up the captcha protection.\n**/config view :** Display the list of settings.\n**/config_set language <language> :** Change the bot's language.\n**/config_set log_channel <#channel>:** Set the bot's log channel.\n**/config_set captcha enabled <true/false>:** Enable or disable configured captcha protection\n**/reverify <@user>:** Make a user re-verify against the captcha.", inline=False) #**{prefix}giveroleaftercaptcha <role ID/off> :** Give a role after that the user passed the captcha.\n**{prefix}minaccountage <number (hours)> :** set a minimum age to join the server (24 hours by default).\n**{prefix}antinudity <true/false> :** Enable or disable the nudity image protection.\n**{prefix}antiprofanity <true/false> :** Enable or disable the profanity protection.\n**{prefix}antispam <true/false> :** Enable or disable the spam protection.\n**{prefix}allowspam <#channel> (remove) :** Enable or disable the spam protection in a specific channel.\n**{prefix}lock | unlock <#channel/ID> :** Lock/Unlock a channel.\n\n**{prefix}kick <@user/ID> :** Kick the user.\n**{prefix}ban <@user/ID> :** ban the user.\n\n**{prefix}changeprefix <prefix> :** Change the bot's prefix.\n", inline=False)
            embed.set_footer(text="Captcha Bot")
            await inter.response.send_message(embed=embed)

# ------------------------ BOT ------------------------ #  

async def setup(bot):
    # bot.remove_command("help")
    await bot.add_cog(HelpCog(bot))