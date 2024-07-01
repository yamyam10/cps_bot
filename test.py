import discord
import os
from discord.ext import commands
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Tesseractのパスを設定（必要に応じて）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Google Sheets APIの設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("just-ratio-368201-5a8966c05bcb.json", scope)
client = gspread.authorize(creds)
spreadsheet_id = "1zTjSr9Dvqt5TlCCgLgaTbj-S399BVuHZ"
spreadsheet = client.open_by_key(spreadsheet_id)

# sheet2を選択
sheet = spreadsheet.worksheet("Sheet2")

# Discordボットの設定
TOKEN = os.getenv('kani_TOKEN')
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

                try:
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
                except gspread.exceptions.APIError as e:
                    await ctx.send(f'APIエラーが発生しました: {e}')
                except Exception as e:
                    await ctx.send(f'エラーが発生しました: {e}')
    else:
        await ctx.send('画像が添付されていません。')

# ボットの起動
bot.run(TOKEN)
