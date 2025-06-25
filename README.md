Captcha Bot is a Discord bot wich allow to protect your discord server without requiring any external integrations (no API tokens or websites).

## Captcha
![](https://github.com/j-mar5/Captcha-Bot/blob/master/Capture1.PNG)

## Installation

Install all dependencies:

* `pip install -r requirements.txt`
* Then put your Discord token that can be found in the Discord's developers portal inside `config.example.json` (do not change anything else)
* Rename it to `config.json`
* This bot needs the "server members intent" and "message content intent" (for now), so you have to enable it in the Discord's developers portal.

Finally, host the bot with `python3 main.py` and invite it to your own server.

## Features

This Discord Bot protect your Discord server with many functions.

* Captcha firewall
* Minimum account age required
* Logs
* Basic moderation commands
* Multi guild support
* Multi language (EN, FR)

Restrictions do not affect members with ADMINISTRATOR permission !

## Logs

![](https://github.com/j-mar5/Captcha-Bot/blob/master/Capture2.PNG)

## Commands

```
?setup <on/off> : Set up the captcha protection.
?settings : Display the list of settings.
?giveroleaftercaptcha <role ID/off> : Give a role after that the user passed the captcha.
?minaccountage <number (hours)> : set a minimum age to join the server (24 hours by default).
?antinudity <true/false> : Enable or disable the nudity image protection.
?antiprofanity <true/false> : Enable or disable the profanity protection.
?antispam <true/false> : Enable or disable the spam protection.
?allowspam <#channel> (False) : Enable or disable the spam protection in a specific channel.
?lock | unlock <#channel> : Lock/Unlock a specific channel.

?userinfos <@user/ID> : Get user infomations.

?ban <@user/ID> : Ban the user.
?kick <@user/ID> : Kick the user.

?changeprefix <prefix> : Change the bot's prefix for the guild.
?changelanguage <language> : Change the bot's language for the guild.
?help : display help.
```

## Potential errors

### ImportError: cannot import name 'joblib' form 'sklearn.externals'
You have to download the last version of profanity_check.
Unstall you current version and download the v1.0.6 with `git+https://github.com/dimitrismistriotis/profanity-check` 

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


## License

This project is under [GPLv3](https://github.com/j-mar5/Captcha-Bot/blob/master/LICENSE).
