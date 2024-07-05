import discord
import os
from discord.ext import commands
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import time
from dotenv import load_dotenv

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
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_resumed(self):
        print('Resumed connection to Discord')

bot = MyBot(command_prefix='!', intents=intents)

def preprocess_image(image_path):
    img = Image.open(image_path)
    # 画像の前処理
    img = img.filter(ImageFilter.SHARPEN)  # シャープ化
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # コントラストを強調
    return img

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def perform_ocr_on_region(image, region):
    cropped_img = image.crop(region)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(cropped_img, lang='jpn+eng', config=custom_config)
    return text.strip()

def filter_valid_data(lines):
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if line and "|" not in line:
            filtered_lines.append(line)
    return filtered_lines

@bot.command(name="試合結果追加")
async def add_match_results(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                for attempt in range(3):  # 3回の再試行を行う
                    try:
                        response = requests.get(attachment.url, timeout=10)
                        response.raise_for_status()
                        img_path = BytesIO(response.content)
                        img = preprocess_image(img_path)

                        try:
                            # 指定された範囲
                            name_region = (235, 1020, 600, 1730)
                            score_region = (270, 660, 870, 860)
                            kills_region = (940, 1020, 1075, 1730)

                            data = []

                            # 名前のテキストを抽出
                            name_text = perform_ocr_on_region(img, name_region)
                            name_lines = filter_valid_data(name_text.split('\n'))
                            print("Name Text:", name_lines)  # デバッグ用

                            # スコアのテキストを抽出
                            score_text = perform_ocr_on_region(img, score_region)
                            score_lines = filter_valid_data(score_text.split('\n'))
                            print("Score Text:", score_lines)  # デバッグ用

                            # キル数のテキストを抽出
                            kills_text = perform_ocr_on_region(img, kills_region)
                            kills_lines = filter_valid_data(kills_text.split('\n'))
                            print("Kills Text:", kills_lines)  # デバッグ用

                            # デバッグ: 各リストの長さを確認
                            print(f"Lengths -> Name: {len(name_lines)}, Score: {len(score_lines)}, Kills: {len(kills_lines)}")

                            for name, score, kills in zip(name_lines, score_lines, kills_lines):
                                clean_score = score.replace("pt", "").strip()
                                if is_number(clean_score) and is_number(kills):
                                    data.append([name, clean_score, kills])
                                    print(f"Valid data found: {name}, {clean_score}, {kills}")

                            # Googleスプレッドシートに書き込み
                            if data:
                                print("Googleスプレッドシートにデータを書き込んでいます。")
                                sheet.clear()
                                sheet.append_row(["名前", "ポータル数", "キル数"])
                                for row in data:
                                    print(f"Appending row: {row}")  # デバッグ用
                                    sheet.append_row(row)
                            else:
                                print("有効なデータが抽出されませんでした。")

                            await ctx.send('データがスプレッドシートに正常に書き込まれました')
                            break  # 成功した場合はループを抜ける
                        except gspread.exceptions.APIError as e:
                            print(f'APIエラーが発生しました: {e}')
                            await ctx.send(f'APIエラーが発生しました: {e}')
                        except Exception as e:
                            print(f'エラーが発生しました: {e}')
                            await ctx.send(f'エラーが発生しました: {e}')
                    except requests.exceptions.RequestException as e:
                        print(f"リクエストエラーが発生しました: {e}. 再試行します...")
                        time.sleep(2 ** attempt)  # 再試行までの待機時間を指数的に増加
                else:
                    await ctx.send('リクエストが失敗しました。後でもう一度試してください。')
    else:
        await ctx.send('画像が添付されていません。')

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
