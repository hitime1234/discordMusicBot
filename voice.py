from discord import FFmpegPCMAudio
from discord.utils import get
from discord.ext.commands import Bot


bot = Bot("God!")

import random 
from pytube import YouTube



import os, struct, discord
bitness = struct.calcsize('P') * 8
target = 'x64' if bitness > 32 else 'x86'
filename = "libopus-0.x64.dll"
os.add_dll_directory(os.getcwd())
discord.opus.load_opus(filename)



from youtube_dl import YoutubeDL
from requests import get as getter
#Get videos from links or from youtube search
def search(query):
    with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
        try: getter(query)
        except: info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else: info = ydl.extract_info(query, download=False)
    return (info, info['formats'][0]['url'])

ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    count = len(bot.guilds)
    print(f'Logged on as {count}, your bot {bot.user} !')

@bot.command()
async def play(ctx):
    channel = ctx.message.author.voice.channel
    temp = ctx.message.content.split(' ')[1]
    print(temp)
    if not channel:
        await ctx.send("You are not connected to a voice channel")
        return
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
                
    #Solves a problem I'll explain later
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    video, source = search(temp)
    voice = get(bot.voice_clients, guild=ctx.guild)

    await ctx.send("Now playing " + temp)
    ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        }
    voice.play(FFmpegPCMAudio(executable="ffmpeg.exe",**ffmpeg_options,source=source))
    voice.is_playing()


@bot.command()
async def leave(ctx): # Note: ?leave won't work, only ?~ will work unless you change  `name = ["~"]` to `aliases = ["~"]` so both can work.
    if (ctx.voice_client): # If the bot is in a voice channel 
        await ctx.guild.voice_client.disconnect() # Leave the channel
        await ctx.send('I have left because of a request')
    else: # But if it isn't
        await ctx.send("I'm not in a voice channel, use the join command to make me join")

try:
    file = open("tokenholder.txt","r")
    token = file.readline()
    file.close()
    bot.run(token)
except:
    print("error no token or invalid")
    file = open("tokenholder.txt","a")
    file.write("ERROR Token is invalid - please delete this after correcting")
    file.close()


