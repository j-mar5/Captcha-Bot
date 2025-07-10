import json

def getConfig(guildID):
    with open("config.json", "r") as config:
        data = json.load(config)
    if str(guildID) not in data["guilds"]:
        defaultConfig = {
            "prefix": "?",
            "language": "en-US",
            "captcha": False,
            "captchaChannel": False,
            "logChannel": False,
            "temporaryRole": False,
            "roleGivenAfterCaptcha": False,
            "minAccountDate": False
        }
        updateConfig(guildID, defaultConfig)
        return defaultConfig
    return data["guilds"][str(guildID)]

def updateConfig(guildID, data):
    with open("config.json", "r") as config:
        config = json.load(config)
    config["guilds"][str(guildID)] = data
    newdata = json.dumps(config, indent=4, ensure_ascii=False)
    with open("config.json", "w") as config:
        config.write(newdata)

async def getGuildPrefix(bot, message):
    if not message.guild:   
        return "?"
    else:
        config = getConfig(message.guild.id)
        return config["prefix"]