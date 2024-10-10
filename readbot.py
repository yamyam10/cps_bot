import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from discord import FFmpegPCMAudio
import asyncio

load_dotenv()

TOKEN = os.getenv('kani_TOKEN')
VOICEVOX_API_URL = "http://127.0.0.1:50021"  # VOICEVOXエンジンがローカルで起動している前提

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'ログインしました {bot.user}')

# 入退室イベントのトリガー
@bot.event
async def on_voice_state_update(member, before, after):
    # ボット自身が接続・切断した場合は処理をスキップ
    if member.id == bot.user.id:
        return

    if before.channel is None and after.channel is not None:
        # ユーザーがチャンネルに参加したとき
        text = f"{member.display_name} がボイスチャンネルに参加しました"
        await generate_and_play_voice(member, text, after.channel)

    elif before.channel is not None and after.channel is None:
        # ユーザーがチャンネルから退出したとき
        text = f"{member.display_name} がボイスチャンネルから退出しました"
        await generate_and_play_voice(member, text, before.channel)

async def generate_and_play_voice(member, text, voice_channel):
    # VOICEVOX APIにテキストを送信して音声合成
    voice_id = 3  # ずんだもんノーマルのID
    audio_query_payload = {"text": text, "speaker": voice_id}

    # 音声クエリ生成
    audio_query_response = requests.post(f"{VOICEVOX_API_URL}/audio_query", params=audio_query_payload)
    audio_query = audio_query_response.json()

    # 音声合成実行
    synthesis_payload = {"speaker": voice_id}
    synthesis_response = requests.post(f"{VOICEVOX_API_URL}/synthesis", json=audio_query, params=synthesis_payload)
    with open("voice_entry_exit.wav", "wb") as f:
        f.write(synthesis_response.content)

    # ボイスチャンネルに接続
    vc = member.guild.voice_client
    if not vc:
        # もしボットがまだ接続されていない場合は接続
        vc = await voice_channel.connect()

    # すでに再生中か確認して、再生中であれば待機
    while vc.is_playing():
        await asyncio.sleep(1)

    # 音声を再生
    vc.play(FFmpegPCMAudio("voice_entry_exit.wav"))
    
    # 再生が終わるまで待機
    while vc.is_playing():
        await asyncio.sleep(1)

    # ボイスチャンネルに誰もいなければ切断
    if len(vc.channel.members) == 1:
        await vc.disconnect()

@bot.command(name="読み上げ", description="ずんだもんの声でメッセージを読み上げ")
async def read_message(ctx):
    if not ctx.author.voice:
        await ctx.send("ボイスチャンネルに接続してください")
        return

    # すでに接続されているか確認
    vc = ctx.voice_client
    if not vc:  # もしボットがまだ接続されていなければ接続する
        vc = await ctx.author.voice.channel.connect()

    embed = discord.Embed(title="読み上げ", url="https://twitter.com/miyavi1117?s=20", color=discord.Color.purple())
    embed.add_field(name="", value="ボイスチャットの接続に成功しました", inline=False)
    await ctx.send(embed=embed)

    try:
        while True:
            message = await bot.wait_for('message', check=lambda m: m.channel == ctx.channel)
            if message.author.bot:
                continue  # ボットのメッセージを無視する

            # VOICEVOX APIにテキストを送信して音声合成
            text = message.content
            voice_id = 3  # ずんだもんノーマルのID
            audio_query_payload = {"text": text, "speaker": voice_id}
            
            # 音声クエリ生成
            audio_query_response = requests.post(f"{VOICEVOX_API_URL}/audio_query", params=audio_query_payload)
            audio_query = audio_query_response.json()

            # 音声合成実行
            synthesis_payload = {"speaker": voice_id}
            synthesis_response = requests.post(f"{VOICEVOX_API_URL}/synthesis", json=audio_query, params=synthesis_payload)
            with open("voice.wav", "wb") as f:
                f.write(synthesis_response.content)

            # すでに再生中か確認して、再生中であれば待機
            while vc.is_playing():
                await asyncio.sleep(1)

            # 音声を再生
            vc.play(FFmpegPCMAudio("voice.wav"))

            # 再生が終わるまで待機
            while vc.is_playing():
                await asyncio.sleep(1)

            # ボイスチャンネルから切断する
            if len(vc.channel.members) == 1:
                await vc.disconnect()
                break
    finally:
        if vc.is_connected():
            await vc.disconnect()

@bot.command(name="切断", description="ボイスチャンネルから切断")
async def disconnect(ctx):
    if not ctx.voice_client:
        embed = discord.Embed(title="ボイスチャンネルに接続していません", color=discord.Color.purple())
        await ctx.send(embed=embed)
        return

    # ボイスチャンネルから切断
    await ctx.voice_client.disconnect()
    embed = discord.Embed(title="切断", url="https://twitter.com/miyavi1117?s=20", color=discord.Color.purple())
    embed.add_field(name="", value="ボイスチャンネルから切断に成功しました", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)