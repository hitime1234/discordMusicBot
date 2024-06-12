import discord
from discord import FFmpegPCMAudio
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import get

#File Handling  
def ReadServerStore(filename):
    filename = filename
    file = open(filename, "r")
    lines = file.readlines()
    TextByGuild = {}
    VoiceByGuild = {}
    for line in lines:
        Text,Voice = line.strip().split(",")
        Guild = line.split(":")[0]
        TextChannel = Text.split(":")[1]
        VoiceChannel = Voice.split(":")[1]
        TextByGuild.update({discord.Object(Guild):int(TextChannel)})
        VoiceByGuild.update({discord.Object(Guild):int(VoiceChannel)})
    file.close()
    return [TextByGuild,VoiceByGuild]

def WriteServerStore(filename,TextByGuild,VoiceByGuild):
    filename = filename
    file = open(filename, "w")
    for key in TextByGuild:
        file.write(str(key.id) + ":" + str(TextByGuild[key]) + "," + str(key.id) + ":" + str(VoiceByGuild[key]) + "\n")
    file.close()
    return True


#needed for discord bot
Bot_GUILDs = []

#for threading loop passthrough
global CurrentChannel,MessageToSend, UserId,ReadyToSend
UserId = 0

ChannelListByGuild,VoiceChannelListByGuild = ReadServerStore("config.conf")


MessageToSend = "`TSP IS online, Love you all <3`"

#Startup Events and Errors logs
lines = open("OptionalChannels.conf","r").read().split("\n")
ErrorChannel = -1
for line in lines:
    if "ErrorChannel" in line:
        ErrorChannel = int(line.split("=")[1])
        break


#dms event
msg_dump_channel = -1
for line in lines:
    if "msg_dump_channel" in line:
        msg_dump_channel = int(line.split("=")[1])
        break



ReadyToSend = True
holder = 0
VoiceStore = 0
searcher = "" 

Queue = []
CurrentPlaying = ""
connector = ""

#EXE 
MusicExecutable = "ffmpeg.exe"

#Holds all Current Voice Channels
class VoiceControl:
    def __init__(self):
        self.VoiceHolder = {}
        self.VoiceRun = {}
        self.VoiceQueue = {}
    
    def AddVoice(self,voice,GuildiD):
        self.VoiceHolder.update({GuildiD:voice})
        self.VoiceRun.update({GuildiD:True})
        self.VoiceQueue.update({GuildiD:[]})
        
    def GetVoice(self,GuildID):
        try:
            return self.VoiceHolder[GuildID]
        except:
            return None
    
    def RemoveVoice(self,GuildID):
        try:
            self.VoiceHolder.pop(GuildID)
            self.VoiceRun.pop(GuildID)
            self.VoiceQueue.pop(GuildID)
        except:
            return None

    def GetVoiceList(self):
        try:
            return self.VoiceHolder
        except:
            return None
        

    #Next song Handler
    def RunNowRunning(self,GuildiD):
        try:
            self.VoiceRun[GuildiD] = False
        except:
            return None

    def RunNowFinished(self,GuildiD):
        try:
            self.VoiceRun[GuildiD] = True
        except:
            return None
        

    def ReturnReadyToRun(self):
        try:
            return [k for k,v in self.VoiceRun.items() if v == True]
        except:
            return None

    #Queue
    def AddVoiceQueue(self,GuildiD,song: str):
        return self.VoiceQueue[GuildiD].append(song)

    def PopVoiceQueue(self,GuildiD,num: int):
        return self.VoiceQueue[GuildiD].pop(num)
    
    def InsertVoiceQueue(self,GuildiD,song: str,num: int):
        return self.VoiceQueue[GuildiD].insert(num,song)

    def ClearVoiceQueue(self,GuildiD):
        return self.VoiceQueue[GuildiD].clear()

    def GetVoiceQueue(self,GuildiD):
        return self.VoiceQueue[GuildiD]


#Updates Guilds
async def SyncGuilds(client):
    print("Syncing commands to the following guilds:")
    async for guild in client.fetch_guilds(limit=150):
            print(guild.name)
            Bot_GUILDs.append(discord.Object(guild.id))
    print("----End of Guilds----\n")



class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)
        
        
    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.

    async def setup_hook(self):
        # This copies the global commands over to all active guilds.
        await SyncGuilds(self)
        
        
        for server in Bot_GUILDs:
            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)


    @tasks.loop(seconds=1)
    async def job(self):
        global ErrorChannel,MessageToSend,ReadyToSend,UserId
        channel = client.get_channel(ErrorChannel)
        if MessageToSend != "":
            await channel.send(MessageToSend)
            MessageToSend = ""
            ReadyToSend = True

    @tasks.loop(seconds=0.5)
    async def MusicJob(self):
        global searcher,VoiceStore
        if len(VoiceStore.ReturnReadyToRun()) != 0:
            for item in VoiceStore.ReturnReadyToRun():
                VoiceStore.RunNowRunning(item)   
                channel = client.get_channel(ChannelListByGuild[item])
                await channel.send("Now playing\n" + CurrentPlaying)
                PlayVoice(item)
                
    
intents = discord.Intents.default()
client = MyClient(intents=intents)

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

@client.event
async def on_ready():
    global holder,searcher,connector,VoiceStore
    #Sets up Default Channel

    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------------------------------------------------')
    client.job.start()
    #Sets up the voice channel
    VoiceStore = VoiceControl()

    #voice = get(client.voice_clients, guild=VoiceChannel)

    # *Auto Start*

    connector = await client.fetch_channel(list(VoiceChannelListByGuild.values())[0])
    voice = await connector.connect()
    holder = voice

    #adds the voice channel to the voice store 
    
    VoiceStore.AddVoice(voice,list(VoiceChannelListByGuild.keys())[0])
    
    #Kahoot music
    temp = "https://www.youtube.com/watch?v=DSZCehssGBo"
    print(temp)
    source = search(temp)
    searcher = source

    #Start Music Player
    client.MusicJob.start() 

    
    #Sets the bot status
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="You're Listening to URY. ON fm, on tap, online, in euro truck simulator and discord "))


@client.event
async def on_message(message: discord.Message):
    channel = client.get_channel(msg_dump_channel)
    if message.guild is None and not message.author.bot:
        # if the channel is public at all, make sure to sanitize this first
        await channel.send(message.author.name + " and with user id: " + str(message.author.id) + " sent me: \n"+ message.content)
    


def PlayVoice(GuildId):
    try:
        global holder,searcher,VoiceStore
        VoiceStore.GetVoice(GuildId).play(FFmpegPCMAudio(executable=MusicExecutable,**FFMPEG_OPTS,source=searcher),after=lambda e: done(GuildId))
    except Exception as e:
        print("OOPS There was a error:\n" + str(e))



def NextInQueue(GuildId):
    global Queue,VoiceStore
    if len(VoiceStore.GetVoiceQueue(GuildId)) == 0:
        return "https://www.youtube.com/watch?v=DSZCehssGBo"
    else:
        return VoiceStore.PopVoiceQueue(GuildId,0)
        #return Queue.pop(0)

def QueueString(GuildId):
    OutputString = ""
    if len(VoiceStore.GetVoiceQueue(GuildId)) == 0:
        return ("The Queue is empty")
    for i in range(0,len(VoiceStore.GetVoiceQueue(GuildId))):
        OutputString = OutputString + str(i) + ". " + VoiceStore.GetVoiceQueue(GuildId)[i] + "\n"
    return OutputString



def done(GuildId):
    global searcher,CurrentPlaying,VoiceStore
    CurrentPlaying = NextInQueue(GuildId)
    print(CurrentPlaying)
    if ("youtube.com/watch?v=" in CurrentPlaying):
        try:
            searcher = search(CurrentPlaying)
        except:
            print("not a valid youtube link")
    else:
        searcher = CurrentPlaying
    VoiceStore.RunNowFinished(GuildId)
        


#Sets next job
def nextjob(msg,userid,channelid):
    global CurrentChannel,MessageToSend,ReadyToSend,UserId
    
    if (ReadyToSend == True and msg.find("<@282224597288615936>") == -1):
        CurrentChannel = channelid
        MessageToSend = msg
        ReadyToSend = False
        UserId = userid
        return True
    else:
        return False

@client.tree.command(name="type",guilds=Bot_GUILDs,description="testcommand")
async def type(interaction: discord.Interaction, str: str):
        if(interaction.user.top_role.permissions.administrator):
            ChannelId = interaction.channel_id 
            UserId = interaction.user.id
            MessageToSend = str
            #threading.Thread(target=nextjob,args=(MessageToSend,UserId,ChannelId,)).start()
            
            #time.sleep(1)
            if (nextjob(MessageToSend,UserId,ChannelId)):
                
                await interaction.response.send_message("Your request has been sent. Please wait")
            else:
                await interaction.response.send_message("Please wait. Request is already being executed please wait and try again")

            #await interaction.followup.send("<@"+ str(UserId) + "> " + str(ChannelId))
        else:
            await interaction.response.send_message("You don't have premission to use this command.\n(Administrator needed)",ephemeral=True)


from requests import get as getter
from youtube_dl import YoutubeDL
def search(query):
    with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
        try: getter(query)
        except Exception as e:
            print(e)
            info = ydl.extract_info(f"ytsearch: " + query, download=False)['entries'][0]
        
        else: info = ydl.extract_info(query, download=False)
    return (info['url'])

ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}



@client.tree.command(name="addtoqueue",description="Adds to the current queue")
async def AddToQueue(interaction: discord.Interaction, string: str):
    global Queue,VoiceStore
    #Queue.append(string)
    VoiceStore.AddVoiceQueue(discord.Object(interaction.guild_id),string)
    await interaction.response.send_message(QueueString(discord.Object(interaction.guild_id)))

@client.tree.command(name="clearqueue",description="Clears the current queue")
async def ClearQueue(interaction: discord.Interaction):
    global Queue,VoiceStore
    #Queue.clear()
    VoiceStore.ClearVoiceQueue(discord.Object(interaction.guild_id))
    await interaction.response.send_message("Queue Cleared")



@client.tree.command(name="showqueue",description="Shows the current queue")
async def ShowQueue(interaction: discord.Interaction):
    global Queue,VoiceStore
    #OutputString = QueueString()
    OutputString = QueueString(discord.Object(interaction.guild_id))
    await interaction.response.send_message(OutputString)

@client.tree.command(name="playury",description="Plays URY FM Feed")
async def playury(interaction: discord.Interaction):
    # adds URY FM to the front of the queue

    #Queue.insert(0,"https://audio.ury.org.uk/fm")
    VoiceStore.InsertVoiceQueue(discord.Object(interaction.guild.id),"https://audio.ury.org.uk/fm",0)

    # skips current song

    VoiceStore.GetVoice(discord.Object(interaction.guild.id)).stop()
    await interaction.response.send_message("Adding URY FM to Queue")

@client.tree.command(name="playuryhq",description="Plays URY High Quality Feed")
async def playuryhq(interaction: discord.Interaction):
    # adds URY HQ to the front of the queue

    #Queue.insert(0,"https://audio.ury.org.uk/live-high")
    VoiceStore.InsertVoiceQueue(discord.Object(interaction.guild.id),"https://audio.ury.org.uk/live-high",0)


    # skips current song
    VoiceStore.GetVoice(discord.Object(interaction.guild.id)).stop()
    await interaction.response.send_message("Adding URY High Quality to Queue")

@client.tree.command(name="skipmusic",description="Ends Current Song")
async def skip(interaction: discord.Interaction):
    """
    Most of the heavy lifting is done by the done function
    """
    VoiceStore.GetVoice(discord.Object(interaction.guild.id)).stop()
    await interaction.response.send_message("Skipping Music")


@client.tree.command(name="pausemusic",description="Pauses Music")
async def pause(interaction: discord.Interaction):
    """
    Pauses the music
    """
    VoiceStore.GetVoice(discord.Object(interaction.guild.id)).pause()
    await interaction.response.send_message("Pausing Music")

@client.tree.command(name="resumemusic",description="Resumes Music")
async def resume(interaction: discord.Interaction):
    """
    Resumes the music
    """
    VoiceStore.GetVoice(discord.Object(interaction.guild.id)).resume()
    await interaction.response.send_message("Resuming Music")


@client.tree.command(name="leave",description="Stops Music Bot")
async def leave(interaction: discord.Interaction):
    global holder,VoiceStore
    VoiceStore.GetVoice(discord.Object(interaction.guild.id)).pause()
    
    #Queue.clear()
    VoiceStore.ClearVoiceQueue(discord.Object(interaction.guild.id))

    await VoiceStore.GetVoice(discord.Object(interaction.guild.id)).disconnect()
    VoiceStore.RemoveVoice(discord.Object(interaction.guild.id))
    await interaction.response.send_message("Stopping Playing Now")


@client.tree.command(name="join",description="Joins Voice Channel")
async def join(interaction: discord.Interaction):
    connector = await client.fetch_channel(VoiceChannelListByGuild[discord.Object(interaction.guild_id)])
    voice = await connector.connect()
    VoiceStore.AddVoice(voice,discord.Object(interaction.guild_id))
    await interaction.response.send_message("Joined Voice Channel")


@client.tree.command(name="help",description="Shows Help")
async def help(interaction: discord.Interaction):
    """
    Shows Help
    """
    await interaction.response.send_message("Commands:\n\n/playury - Plays URY FM\n/playuryhq - Plays URY High Quality\n/skipmusic - Skips Music\n/pausemusic - Pauses Music\n/resumemusic - Resumes Music\n/leave - Leaves Voice Channel\n/join - Joins Voice Channel\n/addtoqueue [link] - Adds to Queue supports (youtube links)\n/clearqueue - Clears Queue\n/showqueue - Shows Queue\n/settextchannel [channel] - Sets Text Channel\n/setvoicechannel [channel] - Sets Voice Channel\n/help - Shows Help")

@client.tree.command(name="settextchannel",description="Sets the channel for the bot commands")
async def SetTextChannel(interaction: discord.Interaction,channel: discord.TextChannel):
    global ChannelListByGuild
    ChannelListByGuild.update({discord.Object(interaction.channel.guild.id):channel.id})
    WriteServerStore("config.conf",ChannelListByGuild,VoiceChannelListByGuild)
    await interaction.response.send_message("Text Channel Set to " + channel.name)

@client.tree.command(name="setvoicechannel",description="Sets the channel for the bot commands")
async def SetVoiceChannel(interaction: discord.Interaction,channel: discord.VoiceChannel):
    global VoiceChannelListByGuild
    VoiceChannelListByGuild.update({discord.Object(interaction.channel.guild.id):channel.id})
    WriteServerStore("config.conf",ChannelListByGuild,VoiceChannelListByGuild)
    await interaction.response.send_message("Voice Channel Set to " + channel.name)

try:
    file = open("Token.txt","r")
    client.run(file.readline().strip())
except Exception as e:
    print("Token File not found\n" + str(e) + "\nPlease create a file called Token.txt with the bot token in it")


