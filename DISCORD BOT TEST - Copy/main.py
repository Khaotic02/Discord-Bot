import random
import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv
import yt_dlp as youtube_dl
from apikeys import *
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotdl
from pytube import YouTube
import json
import webbrowser
import requests
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import sys
import tkinter as tk
from datetime import datetime
import atexit
import re
import asyncio
from discord.ext import commands
from discord.ui import Button, View



intents = discord.Intents.default()
load_dotenv()



filename = ""
queue = []
Spotify = []
intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents)
log_file = "log.txt"  
guild_id = []

@client.event
async def on_message(message):
    if message.channel.is_private:
        await client.send_message(message.channel, "private channel")
        

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,  
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

  
@bot.command(name='join', help='tells the bot to join the voice channel')
async def join(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if not ctx.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.author.name))   
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()


            

spotdl.SpotifyClient.init(client_id='9bfed3b67e4d461095025b427d8a1c1e', client_secret='1d36d2468d2c49cbadbb79e6ff32ff6f')
client_credentials_manager = SpotifyClientCredentials(client_id='9bfed3b67e4d461095025b427d8a1c1e', client_secret='1d36d2468d2c49cbadbb79e6ff32ff6f')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
Disallowed = [398460223163203584]


@bot.command(name='move', help='Move a user to a different voice channel')
async def move_user(ctx, member: discord.Member, channel: discord.VoiceChannel):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this command.")
        return

    await member.move_to(channel)

def cleanup():
    for file in os.listdir('.'):
        if file.endswith('.mp3'):
            os.remove(file)

atexit.register(cleanup)  
            
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected() and len(queue) == 0:
        await voice_client.disconnect()
        while len(queue) >= 0:
            queue.pop(0)
    else:
        await ctx.send("The bot is not connected to a voice channel.")

          
is_downloading = False

@bot.command(name='play', help='To play a song or album in a voice channel')
@commands.cooldown(1, 3, commands.BucketType.user)
async def play_music(ctx, url):
    try:
        global is_downloading

        if ctx.author.id in Disallowed:
            await ctx.send("go fuck yourself")
            return

        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return

        voice_channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client
        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.is_playing() or is_downloading:
            queue.append(url)
            await ctx.send("Added to queue.")
            return

        if "spotify" in url:
            if 'track' in url:
                await play_spotify(ctx, url)
            elif 'album' in url:
                await play_spotify_album(ctx, url)
        else:
            if is_valid_youtube_url(url):
                await play_youtube(ctx, url)
            else:
                await search_youtube(ctx, url)

        if len(queue) > 0:
            next_url = queue.pop(0)
            await play_music(ctx, next_url)
        else:
            is_downloading = False

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\\.(com|be)/'
        '(watch\\?v=|embed/|v/|.+\\?v=)?([^&=%\\?]{11})'
    )
    youtube_match = re.match(youtube_regex, url)
    return youtube_match is not None

async def search_youtube(ctx, query):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(id)s',
            'noplaylist': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch:{query}", download=False)

            if 'entries' in result and result['entries']:
                video_info = result['entries'][0]
                video_title = video_info['title']
                video_id = video_info['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                embed = discord.Embed(title="Found Song", description=f"Found the following song: {video_title}",
                                      color=0x1DB954)
                await ctx.send(embed=embed)

                queue.append(video_url)

                voice_client = ctx.guild.voice_client
                if not voice_client.is_playing() and not voice_client.is_paused() and len(queue) == 1:
                    next_url = queue.pop(0)
                    await play_music(ctx, next_url)
            else:
                await ctx.send("No results found.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

async def play_youtube(ctx, url):
    try:
        global is_downloading

        with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title')
            video_author = info.get('uploader') if 'uploader' in info else 'Unknown Channel'
            video_thumbnail = info.get('thumbnail')

        embed = discord.Embed(title="Downloading", description="Downloading the video...", color=0xFF0000)
        embed.set_thumbnail(url=video_thumbnail)
        embed.add_field(name="Channel", value=video_author, inline=False)
        status_message = await ctx.send(embed=embed)

        filename = await YTDLSource.from_url(url, loop=bot.loop)

        embed.title = "Now playing"
        embed.description = ""
        embed.add_field(name="Song:", value=video_title, inline=False)
        embed.set_thumbnail(url=video_thumbnail)
        await status_message.edit(embed=embed)

        voice_client = ctx.guild.voice_client

        if is_downloading:
            queue.append(url)
        else:
            is_downloading = True
            voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))

            while voice_client.is_playing() or voice_client.is_paused():
                await asyncio.sleep(1)

            os.remove(filename)
            is_downloading = False

            if len(queue) > 0:
                next_url = queue.pop(0)
                await play_music(ctx, next_url)

            embed.title = "Queue is empty"
            embed.clear_fields()
            embed.set_thumbnail(url="")
            await status_message.edit(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

async def play_spotify_album(ctx, url):
    try:
        global is_downloading

        playlist_info = sp.album(url)
        playlist_name = playlist_info['name']
        playlist_tracks = playlist_info['tracks']['items']
        playlist_url = playlist_info['external_urls']['spotify']
        voice_client = ctx.guild.voice_client

        for track in playlist_tracks:
            track_url = track['external_urls']['spotify']
            queue.append(track_url)

        if voice_client.is_playing() or voice_client.is_paused():
            return

        next_url = queue.pop(0)
        await play_music(ctx, next_url)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

async def play_spotify(ctx, url):
    try:
        global is_downloading

        track_id = url.split('/')[-1].split('?')[0]
        track_info = sp.track(track_id)
        track_name = track_info['name']
        track_artist = track_info['artists'][0]['name']
        track_url = track_info['external_urls']['spotify']
        track_image = track_info['album']['images'][0]['url']

        embed = discord.Embed(title="Downloading", description="Downloading the song...", color=0x1DB954)
        embed.set_thumbnail(url=track_image)
        status_message = await ctx.send(embed=embed)

        command = f'spotdl --bitrate 320k {url}'
        subprocess.run(command, shell=True, check=True)

        filename = None
        for file in os.listdir('.'):
            if file.endswith('.mp3'):
                filename = file
                break

        if filename:
            voice_client = ctx.guild.voice_client

            if is_downloading:
                queue.append(url)
            else:
                is_downloading = True
                embed.title = "Now playing"
                embed.description = ""
                embed.add_field(name="Song:", value=track_name, inline=False)
                embed.add_field(name="Artist:", value=track_artist, inline=False)
                embed.set_thumbnail(url=track_image)
                await status_message.edit(embed=embed)

                voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))

                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1)

                os.remove(filename)
                is_downloading = False

                if len(queue) > 0:
                    next_url = queue.pop(0)
                    await play_music(ctx, next_url)

                embed.title = "Queue is empty"
                embed.clear_fields()
                embed.set_thumbnail(url="")
                await status_message.edit(embed=embed)
                

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    except spotipy.SpotifyException as e:
        print(f"Spotify API Error: {e}")


                
@bot.command(name='pause', help='To pause the song')
async def pause(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Song paused.")
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Song resumed.")
    else:
        await ctx.send("The bot was not playing anything before this. Use the play command.")
     
@bot.command(name='skip', help='skips the song')
async def skip(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if len(queue) > 0:
        voice_client = ctx.guild.voice_client
        voice_client.stop()
        await ctx.send("Skipping the song...")
        next_url = queue.append(0)
        os.remove(filename)
        await play_music(ctx, next_url)
    else:
        await ctx.send("there is no queue use the '!stop' command")



@bot.command(name='stop', help='To stop the song')
async def stop(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Song stopped.")
    else:
        await ctx.send("The bot is not playing anything at the moment.")
 
playlist_data_file = 'playlist_data.json'
playlists = {}  


def save_playlist_data():
    with open(playlist_data_file, 'w') as file:
        json.dump(playlists, file)

def load_playlist_data():
    global playlists
    try:
        with open(playlist_data_file, 'r') as file:
            playlists = json.load(file)
    except FileNotFoundError:
        playlists = {}


def update_playlist(playlist_name):
    save_playlist_data()
    load_playlist_data()

load_playlist_data()






async def auto_disconnect(ctx):
    await asyncio.sleep(300)  
    
    voice_client = ctx.guild.voice_client
    if voice_client and not voice_client.is_playing(): 
        await voice_client.disconnect()
        await ctx.send("Disconnected due to inactivity.")


@bot.command(name='create_playlist', help='Create a new playlist')
async def create_playlist(ctx, playlist_name):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if playlist_name in playlists:
        await ctx.send(f"Playlist '{playlist_name}' already exists.")
    else:
        playlists[playlist_name] = []
        update_playlist(playlist_name)
        await ctx.send(f"Playlist '{playlist_name}' created successfully.")

@bot.command(name='add_to_playlist', help='Add a song to a playlist')
async def add_to_playlist(ctx, playlist_name, song_url):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if playlist_name not in playlists:
        await ctx.send(f"Playlist '{playlist_name}' does not exist.")
    else:
        playlists[playlist_name].append(song_url)
        update_playlist(playlist_name)
        await ctx.send("Song added to the playlist.")

@bot.command(name='remove_from_playlist', help='Remove a song from a playlist')
async def remove_from_playlist(ctx, playlist_name, song_index):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if playlist_name not in playlists:
        await ctx.send(f"Playlist '{playlist_name}' does not exist.")
    else:
        try:
            song_index = int(song_index) - 1
            playlist = playlists[playlist_name]
            if song_index < 0 or song_index >= len(playlist):
                await ctx.send("Invalid song index.")
            else:
                removed_song = playlist.pop(song_index)
                update_playlist(playlist_name)
                await ctx.send(f"Song '{removed_song}' removed from the playlist.")
        except ValueError:
            await ctx.send("Invalid song index.")

@bot.command(name='list_playlists', help='List all created playlists')
async def list_playlists(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    
    if not playlists:
        await ctx.send("There are no playlists created yet.")
    else:
        embed = discord.Embed(title="Created Playlists", color=discord.Color.blue())

        for playlist_name in playlists:
            playlist = playlists[playlist_name]
            song_count = len(playlist)
            embed.add_field(name=f"Playlist: {playlist_name}", value=f"Number of Songs: {song_count}", inline=False)

        await ctx.send(embed=embed)


@bot.command(name='list_songs', help='List songs in a playlist')
async def list_songs(ctx, playlist_name):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if playlist_name not in playlists:
        await ctx.send(f"Playlist '{playlist_name}' does not exist.")
    else:
        playlist = playlists[playlist_name]
        if not playlist:
            await ctx.send(f"The playlist '{playlist_name}' is empty.")
        else:
            embeds = []
            for index, song_url in enumerate(playlist):
                song_details = get_song_details(song_url)
                if song_details:
                    embed = discord.Embed(title=f"Songs in '{playlist_name}'", color=discord.Color.blue())
                    embed.set_thumbnail(url=song_details['image_url'])
                    embed.add_field(name=f"Song {index + 1}", value=f"{song_details['title']} by {song_details['artist']}", inline=False)
                    embeds.append(embed)
            
            if not embeds:
                await ctx.send(f"No song details available for the playlist '{playlist_name}'.")
            else:
                current_page = 0
                message = await ctx.send(embed=embeds[current_page])
                await message.add_reaction('⬅️')
                await message.add_reaction('➡️')
    
                def check(reaction, user):
                    return (
                        user == ctx.author
                        and reaction.message.id == message.id
                        and reaction.emoji in ['⬅️', '➡️']
                    )
    
                while True:
                    try:
                        reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=60.0)
                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break
    
                    if reaction.emoji == '⬅️':
                        current_page = (current_page - 1) % len(embeds)
                    elif reaction.emoji == '➡️':
                        current_page = (current_page + 1) % len(embeds)
    
                    await message.edit(embed=embeds[current_page])
                    await reaction.remove(ctx.author)

def get_song_details(song_url):
    track_id = song_url.split('/')[-1].split('?')[0]
    try:
        track_info = sp.track(track_id)
        track_name = track_info['name']
        track_artist = track_info['artists'][0]['name']
        track_image = track_info['album']['images'][0]['url']
        
        return {
            'title': track_name,
            'artist': track_artist,
            'image_url': track_image
        }
    except spotipy.exceptions.SpotifyException:
        return None



@bot.command(name='delete_playlist', help='Delete a playlist')
async def delete_playlist(ctx, playlist_name):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    
    if playlist_name not in playlists:
        await ctx.send(f"Playlist '{playlist_name}' does not exist.")
    else:
        del playlists[playlist_name]
        update_playlist(playlist_name)
        
        playlist_file = f"{playlist_name}.json"
        if os.path.exists(playlist_file):
            os.remove(playlist_file)
        
        await ctx.send(f"Playlist '{playlist_name}' has been deleted.")
        
        
        
@bot.command(name='play_playlist', help='Play songs from a playlist')
async def play_playlist(ctx, playlist_name):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if playlist_name not in playlists:
        await ctx.send(f"Playlist '{playlist_name}' does not exist.")
        return

    playlist = playlists[playlist_name]
    if not playlist:
        await ctx.send(f"The playlist '{playlist_name}' is empty.")
        return

    voice_client = ctx.guild.voice_client
    if not voice_client:
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()

    for song_url in playlist[1:]:
        queue.append(song_url)

    if not voice_client.is_playing() and playlist:
        await play_music(ctx, playlist[0])
        await ctx.send(f"Playing the first song from '{playlist_name}'")

    await ctx.send(f"All songs from '{playlist_name}' added to the queue")




@bot.command(name='shuffle_playlist', help='Shuffle the songs in a playlist')
async def shuffle_playlist(ctx, playlist_name):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    if playlist_name not in playlists:
        await ctx.send(f"Playlist '{playlist_name}' does not exist.")
        return

    playlist = playlists[playlist_name]
    if not playlist:
        await ctx.send(f"The playlist '{playlist_name}' is empty.")   
        return

    random.shuffle(playlist)

    await ctx.send(f"The songs in the playlist '{playlist_name}' have been shuffled.")
    



user = ""

@bot.command(name='queue', help='Display the current song queue')
async def display_queue(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return

    if not queue:
        await ctx.send("The queue is empty.")
        return

    currently_playing = None
    if len(queue) > 0:
        currently_playing = queue[0]
    else: 
        await auto_disconnect(ctx)
    
    embeds = []
    for index, song in enumerate(queue):
        embed = discord.Embed(title="Music Queue", color=discord.Color.blue())

        if song.startswith('https://open.spotify.com/'):
            try:
                track_info = sp.track(song.split('/')[-1].split('?')[0])
                track_name = track_info['name']
                track_artist = track_info['artists'][0]['name']
                track_image = track_info['album']['images'][0]['url']

                embed.add_field(name=f"Song {index + 1}", value=f"{track_name} by {track_artist}", inline=False)
                embed.set_thumbnail(url=track_image)
            except spotipy.SpotifyException:
                continue
        elif song.startswith('https://www.youtube.com/'):
            video_title, video_thumbnail = get_video_details(song)

            embed.add_field(name=f"Video {index + 1}", value=video_title, inline=False)
            embed.set_thumbnail(url=video_thumbnail)
        else:
            embed.add_field(name=f"Invalid URL", value=song, inline=False)

        embeds.append(embed)

    if not embeds:
        await ctx.send("The queue is empty.")
        return

    current_page = 0
    message = await ctx.send(embed=embeds[current_page])
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')
    await message.add_reaction('⏯️')
    await message.add_reaction('⏭️')
    await message.add_reaction('❌')
    await message.add_reaction('🔀')
    await message.add_reaction('📃') 


    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id

    while True:
        try:
            reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break

        if reaction.emoji == '⬅️':
            current_page = (current_page - 1) % len(embeds)
        elif reaction.emoji == '➡️':
            current_page = (current_page + 1) % len(embeds)
        elif reaction.emoji == '⏯️':
            is_playing = await check_status(ctx)
            if is_playing:
                await pause(ctx)
            else:
                await resume(ctx)
        elif reaction.emoji == '⏭️':
            if currently_playing:
                await skip(ctx)
        elif reaction.emoji == '❌':
            if current_page < len(embeds):
                removed_song = queue.pop(current_page)
                embeds.pop(current_page)
            if current_page >= len(embeds):
                current_page = max(0, len(embeds) - 1)
            if embeds:
                await message.edit(embed=embeds[current_page])
            else:
                await message.edit(content="The queue is empty.")
        elif reaction.emoji == '🔀':
            random.shuffle(queue)
            embeds.clear()
        elif reaction.emoji == '📃':
            queue_list = generate_queue_list(queue)
            await ctx.send(f"**Current Queue:**\n{queue_list}")

            


            for index, song in enumerate(queue):
                embed = discord.Embed(title="Music Queue", color=discord.Color.blue())

                if song.startswith('https://open.spotify.com/'):
                    try:
                        track_info = sp.track(song.split('/')[-1].split('?')[0])
                        track_name = track_info['name']
                        track_artist = track_info['artists'][0]['name']
                        track_image = track_info['album']['images'][0]['url']

                        embed.add_field(name=f"Song {index + 1}", value=f"{track_name} by {track_artist}", inline=False)
                        embed.set_thumbnail(url=track_image)
                    except spotipy.SpotifyException:
                        continue
                elif song.startswith('https://www.youtube.com/'):
                    video_title, video_thumbnail = get_video_details(song)

                    embed.add_field(name=f"Video {index + 1}", value=video_title, inline=False)
                    embed.set_thumbnail(url=video_thumbnail)
                else:
                    embed.add_field(name=f"Invalid URL", value=song, inline=False)

                embeds.append(embed)

            if not embeds:
                await message.edit(content="The queue is empty.")
                break

            current_page = 0
            await message.edit(embed=embeds[current_page])

        await reaction.remove(ctx.author)
        await message.edit(embed=embeds[current_page])

def generate_queue_list(queue):
    if not queue:
        return "The queue is empty."
    
    song_list = []
    for idx, song in enumerate(queue):
        if song.startswith('https://open.spotify.com/'):
            try:
                track_info = sp.track(song.split('/')[-1].split('?')[0])
                track_name = track_info['name']
                track_artist = track_info['artists'][0]['name']
                song_list.append(f"{idx + 1}. {track_name} by {track_artist}")
            except spotipy.SpotifyException:
                song_list.append(f"{idx + 1}. [Error retrieving song info]")
        elif song.startswith('https://www.youtube.com/'):
            video_title, _ = get_video_details(song)
            song_list.append(f"{idx + 1}. {video_title}")
        else:
            song_list.append(f"{idx + 1}. Invalid URL")
    
    return '\n'.join(song_list)

        
   
def get_video_details(url):
    with youtube_dl.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get('title')
        video_thumbnail = info.get('thumbnail')
        return video_title, video_thumbnail


@bot.command(name='status', help='Check if the bot is playing audio in a voice channel')
async def check_status(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        return True
    else:
        return False
        
        
@bot.command(name='test', help='what do you think test means?')
async def test(ctx):
    embed = discord.Embed(title='Queue Display', description='This is the queue display.')

    embed.add_field(name='Click Me', value='Click the button to proceed.')

    message = await ctx.send(embed=embed)

    await message.add_reaction('👍')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == '👍'

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('You did not click the button in time.')
    else:
        embed.set_field_at(0, name='Button Clicked', value='You clicked the button!')

        await message.clear_reactions()

        await message.edit(embed=embed)
            
@bot.command(name='clearbot', help='clear the bots chatlogs')
async def clearbot(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this bot.")
        return
    def is_bot(m):
        return m.author == bot.user

    deleted = await ctx.channel.purge(limit=100, check=is_bot)
    await ctx.send(f"Deleted {len(deleted)} bot messages.")


@bot.command(name='restart', help='Restart the bot')
async def restart_bot(ctx):
    if ctx.author.id in Disallowed:
        await ctx.send("You are not authorized to use this command.")
        return

    await ctx.send("Restarting the bot...")
    

    python = sys.executable
    subprocess.Popen(["python3", "main.py"])
    sys.exit()

gender_roles = [("💪", "Male"), 
                ("💋", "Female"), 
                ("🖖", "Other")]


notifications_roles = [("🟦", "Events n Competitions"), 
                       ("🟩", "Voice Seshs n Vibes"),
                       ("🍁", "Looking to Smoke in The Main Box"), 
                       ("🍻", "Drinking Seshs n Shots"), 
                       ("⚡", "Quick Seshs")]

poison_roles = [("🌿", "Cannabis"), 
                ("🍷", "Alcohol"), 
                ("🍄", "Psychedelics")]

region_roles = [("🇺🇸", "North America"), 
                ("🇧🇷", "South America"), 
                ("🇯🇵", "Asia"), 
                ("🇬🇷", "Europe"), 
                ("🇦🇺", "Oceania"), 
                ("🇿🇦", "Africa")]

embed_notifications = discord.Embed(title="Pick Your Notifications", color=discord.Color.blue())
for emoji, role in notifications_roles:
    embed_notifications.add_field(name=f"{emoji} {role}", value="React to select", inline=False)

embed_poison = discord.Embed(title="Pick Your Poison", color=discord.Color.green())
for emoji, role in poison_roles:
    embed_poison.add_field(name=f"{emoji} {role}", value="React to select", inline=False)

embed_region = discord.Embed(title="Pick Your Region", color=discord.Color.purple())
for emoji, role in region_roles:
    embed_region.add_field(name=f"{emoji} {role}", value="React to select", inline=False)

@bot.command(name="role_menu")
async def display_roles(ctx):
    view_notifications = View()
    for emoji, role in notifications_roles:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=f"notification_{role}")
        view_notifications.add_item(button)

    view_poison = View()
    for emoji, role in poison_roles:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=f"poison_{role}")
        view_poison.add_item(button)

    view_region = View()
    for emoji, role in region_roles:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=f"region_{role}")
        view_region.add_item(button)

    message_notifications = await ctx.send(embed=embed_notifications, view=view_notifications)
    message_poison = await ctx.send(embed=embed_poison, view=view_poison)
    message_region = await ctx.send(embed=embed_region, view=view_region)



bot.run(TOKEN)  