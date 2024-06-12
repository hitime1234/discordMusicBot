# DiscordMusicBot
 Now Supports Multi Server Threads, music Bot for discord with ability to play youtube streams and icecast streams.
 - Version 2.0 - Supports many new features

## SETUP

# Python Requirements
- python version 3.x
- discord.py, youtube_dl, requests

# Windows:

You will to download ffmpeg.exe from https://ffmpeg.org/download.html#build-windows

# Linux:

remove `MusicExecutable` variable from the python Script on linux 

and install ffmpeg from your package manager:

https://ffmpeg.org/download.html#build-linux


### Required Files

## Token.txt
Used to hold the token of your discord bot

# Format 

`YOURTOKEN`


## Config.conf
Used to Store Channel IDs of servers.

# Format

`GUILD:TEXTCHANNELID,GUILD:VOICECHANNELID`

### OptionalChannels.conf
Used to send Bot logs to a discord channel.

# Format

```
msg_dump_channel=INSERTIDHERE
ErrorChannel=INSERTIDHERE
```



