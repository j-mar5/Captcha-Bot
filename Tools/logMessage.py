import json
from discord import Forbidden
from Tools.utils import getConfig, updateConfig

async def sendLogMessage(self, event, channel, embed, messageFile=None):
    """Send the message in the log channel"""
    
    if channel is False:
        # Logs are disabled
        return 

    if isinstance(channel, int):
        # It is a channel id
        channel = self.bot.get_channel(channel)

    if channel is None:
        # Channel is deleted
        try:
            channel = await event.guild.create_text_channel(f"{self.bot.user.name}-logs")

            perms = channel.overwrites_for(event.guild.default_role)
            perms.read_messages=False
            await channel.set_permissions(event.guild.default_role, overwrite=perms)
        except Forbidden:
            return await event.channel.send(f"**Log error :** Cannot create a log channel.")

        # Get configuration.json data 
        data = getConfig(channel.guild.id)
        data["logChannel"] = channel.id

        # Edit configuration.json
        
        updateConfig(channel.guild.id, data)

    # Send the message
    await channel.send(embed=embed, file=messageFile)