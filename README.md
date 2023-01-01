# gh-gist-bot

Bot network using github gists as a comm channel - CTU intro to security course

## Controller usage:

Bot controller script, connect to given gist channel and send commands

```
usage: controller.py [options] gist-id

positional arguments:
  gist-id                Github gist id

options:
  -h, --help            show this help message and exit
  -t TOKEN, --token TOKEN
                        Github personal access token, required if not
                        specified in .env file
  -d, --delete          Delete all comments

cli usage:
    "post": create comment with text and bot command - this wil create a comment and use it for all subsequent commands
    "command": submit a bot command - this wil use last command comment or create a new one with random message
        <any unix command>: send unix command to be called by bots
        "clear": command bots to delete their comments
        "get": get a base64-encoded file from bots machine
    "commands": show commands and responses
    "results": show bot responses
    "bots": show active bot count
    "clear": delete controller comments
    "comments": show gist comments
    "exit": quit application
```

## Bot usage

Bot script listening to commands on given gist channel

```
usage: bot.py [-h] [-v] [-p POLL_INTERVAL] [-t TOKEN] gist-id

positional arguments:
  gistId                Github gist id

options:
  -h, --help            show this help message and exit
  -v, --verbose         Show logs
  -p POLL_INTERVAL, --poll-interval POLL_INTERVAL
                        Set polling frequency
  -t TOKEN, --token TOKEN
                        Github personal access token, required if not specified in
                        .env file
```
