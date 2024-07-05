import discord
import os
from discord.ext import commands
import pytesseract
from PIL import Image, ImageFilter
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
    # グレースケールに変換しない
    img = img.filter(ImageFilter.SHARPEN)  # シャープ化
    return img

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def perform_ocr_on_region(image, region):
    # 指定した領域を切り出し
    cropped_img = image.crop(region)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(cropped_img, lang='jpn', config=custom_config)
    return text.strip()

@bot.command(name="試合結果追加")
async def add_match_results(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                response = requests.get(attachment.url)
                img_path = BytesIO(response.content)
                img = preprocess_image(img_path)

                try:
                    # 指定された範囲
                    name_region = (240, 1020, 600, 1730)
                    score_region = (270, 660, 870, 860)
                    kills_region = (940, 1020, 1075, 1730)

                    data = []

                    # 名前のテキストを抽出
                    name_text = perform_ocr_on_region(img, name_region)
                    name_lines = name_text.split('\n')

                    # スコアのテキストを抽出
                    score_text = perform_ocr_on_region(img, score_region)
                    score_lines = score_text.split('\n')

                    # キル数のテキストを抽出
                    kills_text = perform_ocr_on_region(img, kills_region)
                    kills_lines = kills_text.split('\n')

                    for name, score, kills in zip(name_lines, score_lines, kills_lines):
                        if is_number(score.replace("", "")) and is_number(kills):
                            data.append([name, score.replace("", ""), kills])

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
