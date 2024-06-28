import discord
from discord.ext import commands
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Google Sheets APIの設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("path/to/your/credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Your Spreadsheet Name")
sheet = spreadsheet.sheet1

# Discordボットの設定
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# コマンドハンドラの追加
@bot.command(name="試合結果追加")
async def add_match_results(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                response = requests.get(attachment.url)
                img = Image.open(BytesIO(response.content))

                # OCR処理
                text = pytesseract.image_to_string(img, lang='jpn')

                # テキストの解析
                lines = text.split('\n')
                data = []
                for line in lines:
                    if "pt" in line:
                        parts = line.split()
                        name = parts[0]
                        score = parts[1].replace("pt", "")
                        kills = parts[-1]
                        data.append([name, score, kills])

                # Googleスプレッドシートに書き込み
                sheet.clear()
                sheet.append_row(["名前", "スコア", "キル数"])
                for row in data:
                    sheet.append_row(row)

                await ctx.send('データがスプレッドシートに正常に書き込まれました')
    else:
        await ctx.send('画像が添付されていません。')

# ボットの起動
bot.run(TOKEN)
