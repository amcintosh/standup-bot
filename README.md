# standup-bot
Slack bot to remind team of standups.

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/amcintosh/standup-bot)

## Usage

- Create a imgur gallery of any images you want posted for standup.
- set the environment variables for imgur, slack, etc.
- Configure heroku scheduler to run `python standup-bot.py` at the time of your team's standup.

Commands:
- `!standup` - Call for standup, resetting any delay.
- `!standup delay` - Prevent the next scheduled standup message until manually called.