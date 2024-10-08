import discord, os
from discord.ext import commands
import yt_dlp
import asyncio
from dotenv import load_dotenv
from collections import deque

load_dotenv()

TOKEN = os.getenv('kani_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

audio_cache = {}

@bot.event
async def on_ready():
    print(f'ログインしました {bot.user}')

voice_clients = {}
music_queue = {}
now_playing = {}

yt_dl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': 'True',
    'quiet': True,
    'no_warnings': True
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

async def get_youtube_audio(url):
    if url in audio_cache:
        return audio_cache[url]

    loop = asyncio.get_event_loop()

    try:
        data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(yt_dl_opts).extract_info(url, download=False))

        formats = data.get('formats')
        audio_url = None

        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_url = f.get('url')
                break

        if audio_url is None:
            raise ValueError("音声フォーマットが見つかりませんでした。")

        title = data.get('title', 'タイトル不明')

        audio_cache[url] = (audio_url, title)

        return audio_url, title

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise e

@bot.event
async def on_voice_state_update(member, before, after):
    # 誰かがボイスチャンネルから退出したかを確認
    if before.channel is not None and len(before.channel.members) == 0:
        voice_client = voice_clients.get(member.guild.id)
        if voice_client is not None and voice_client.is_connected():
            # メンバーが誰もいない場合、ボイスチャンネルから切断
            await voice_client.disconnect()
            del voice_clients[member.guild.id]
            del music_queue[member.guild.id]
            del now_playing[member.guild.id]

            channel = bot.get_channel(before.channel.id)
            embed = discord.Embed(title="Disconnected", description="誰も通話にいないため、ボイスチャンネルから切断しました。", color=discord.Color.red())
            await channel.send(embed=embed)

async def play_next(ctx):
    # 通話に誰もいない場合、退出
    voice_client = voice_clients.get(ctx.guild.id)
    if voice_client is not None and len(voice_client.channel.members) == 1:  # botだけが残っている場合
        await voice_client.disconnect()
        embed = discord.Embed(title="Disconnected", description="誰も通話にいないため、ボイスチャンネルから切断しました。", color=discord.Color.red())
        await ctx.send(embed=embed)

        del voice_clients[ctx.guild.id]
        del music_queue[ctx.guild.id]
        del now_playing[ctx.guild.id]
        return

    if len(music_queue[ctx.guild.id]) > 0:
        next_song = music_queue[ctx.guild.id].popleft()
        stream_url, title = await get_youtube_audio(next_song)
        voice_client = voice_clients[ctx.guild.id]
        now_playing[ctx.guild.id] = title

        def after_playing(e):
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

        voice_client.play(discord.FFmpegPCMAudio(stream_url, **ffmpeg_options), after=after_playing)
        
        embed = discord.Embed(title="再生中", description=f"{title}", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        if ctx.voice_client and ctx.voice_client.is_connected():
            await voice_clients[ctx.guild.id].disconnect()
            embed = discord.Embed(title="Disconnected", description="再生リストが空のため、ボイスチャンネルから切断しました。", color=discord.Color.red())
            await ctx.send(embed=embed)

        if len(music_queue[ctx.guild.id]) == 0:
            embed_empty = discord.Embed(title="再生リストが空", description="すべての曲の再生が完了しました。再生リストが空です。", color=discord.Color.red())
            await ctx.send(embed=embed)

        del voice_clients[ctx.guild.id]
        del music_queue[ctx.guild.id]
        del now_playing[ctx.guild.id]

@bot.command(name='play', aliases=['p'], help='YouTubeのリンクを使って音楽を再生します')
async def play(ctx, url: str):
    try:
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            voice_client = await voice_channel.connect()
            voice_clients[ctx.guild.id] = voice_client
            music_queue[ctx.guild.id] = deque()
            now_playing[ctx.guild.id] = None
        else:
            voice_client = voice_clients[ctx.guild.id]

        music_queue[ctx.guild.id].append(url)

        if not voice_client.is_playing():
            try:
                stream_url, title = await get_youtube_audio(music_queue[ctx.guild.id].popleft())
            except Exception as e:
                embed = discord.Embed(title="Error", description="YouTubeから音楽を取得できませんでした。", color=discord.Color.red())
                await ctx.send(embed=embed)
                return

            now_playing[ctx.guild.id] = title
            voice_client.play(discord.FFmpegPCMAudio(stream_url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

            embed = discord.Embed(title="再生中", description=f"{title}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="再生リストに追加", description=f"{url} を再生リストに追加しました。", color=discord.Color.blue())
            await ctx.send(embed=embed)

    except AttributeError:
        embed = discord.Embed(title="Error", description="ボイスチャンネルに参加してからコマンドを使用してください。", color=discord.Color.red())
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        embed = discord.Embed(title="Error", description="エラーが発生しました。", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='skip', aliases=['s'], help='現在の曲をスキップして次の曲を再生します')
async def skip(ctx):
    try:
        voice_client = voice_clients.get(ctx.guild.id)

        if voice_client and voice_client.is_playing():
            skipped_title = now_playing.get(ctx.guild.id, "不明")
            voice_client.stop()

            embed_skip = discord.Embed(title="スキップ", description=f"{skipped_title} をスキップしました。", color=discord.Color.orange())
            await ctx.send(embed=embed_skip)
        else:
            embed_no_song = discord.Embed(title="", description="現在再生中の曲はありません。", color=discord.Color.red())
            await ctx.send(embed=embed_no_song)

    except Exception as e:
        print(e)
        embed_error = discord.Embed(title="Error", description="エラーが発生しました。", color=discord.Color.red())
        await ctx.send(embed=embed_error)

bot.run(TOKEN)
