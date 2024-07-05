import discord
import os
from discord.ext import commands
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
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
spreadsheet_id = "1au449fTjlaDdiRriPN5OvDeBUc4-yWJQguPfvqMmmhw"

try:
    # スプレッドシートを開く
    print("スプレッドシートを開いています...")
    spreadsheet = client.open_by_key(spreadsheet_id)
    print("スプレッドシートが正常に開かれました。")

    # sheet2を選択
    try:
        sheet = spreadsheet.worksheet("Sheet2")
        print("Sheet2が正常に選択されました。")
    except gspread.exceptions.WorksheetNotFound:
        # シートが存在しない場合は作成
        sheet = spreadsheet.add_worksheet(title="Sheet2", rows="100", cols="20")
        print("Sheet2が作成されました。")

except gspread.exceptions.APIError as e:
    print(f'APIエラーが発生しました: {e}')
    if 'not supported' in str(e):
        print("ドキュメント形式がサポートされていない可能性があります。")
    exit()
except Exception as e:
    print(f'一般的なエラーが発生しました: {e}')
    print(f'詳細: {str(e)}')
    exit()

# Discordボットの設定
TOKEN = os.getenv('kani_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def preprocess_image(image_path):
    img = Image.open(image_path)
    img = img.convert('L')  # グレースケールに変換
    img = img.filter(ImageFilter.SHARPEN)  # シャープ化
    img = img.point(lambda x: 0 if x < 140 else 255, '1')  # バイナリ化
    img = img.resize((img.width * 2, img.height * 2))  # 解像度を2倍にする
    return img

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# コマンドハンドラの追加
@bot.command(name="試合結果追加")
async def add_match_results(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                response = requests.get(attachment.url)
                img_path = BytesIO(response.content)
                img = preprocess_image(img_path)

                try:
                    # OCR処理
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(img, lang='jpn', config=custom_config)
                    print("OCR処理が完了しました。抽出されたテキスト：")
                    print(text)

                    # テキストの解析
                    lines = text.split('\n')
                    data = []
                    for line in lines:
                        if line.strip():  # 空行を除去
                            parts = line.split()
                            if len(parts) >= 3 and is_number(parts[-2].replace("pt", "")) and is_number(parts[-1]):
                                name = " ".join(parts[:-2])
                                score = parts[-2].replace("pt", "")
                                kills = parts[-1]
                                data.append([name, score, kills])

                    # Googleスプレッドシートに書き込み
                    print("Googleスプレッドシートにデータを書き込んでいます。")
                    sheet.clear()
                    sheet.append_row(["名前", "ポータル数", "キル数"])
                    for row in data:
                        sheet.append_row(row)

                    await ctx.send('データがスプレッドシートに正常に書き込まれました')
                except gspread.exceptions.APIError as e:
                    print(f'APIエラーが発生しました: {e}')
                    await ctx.send(f'APIエラーが発生しました: {e}')
                except Exception as e:
                    print(f'エラーが発生しました: {e}')
                    await ctx.send(f'エラーが発生しました: {e}')
    else:
        await ctx.send('画像が添付されていません。')

# ボットの起動
bot.run(TOKEN)
