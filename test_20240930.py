import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
import discord
import asyncio
import pytesseract
from dotenv import load_dotenv

# Tesseractのパスを設定（必要に応じて）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
load_dotenv()
# 環境変数から認証情報を取得
private_key = os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n")  # 改行のエスケープ処理
creds_data = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": private_key,
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('GOOGLE_CLIENT_EMAIL')}"
}

# 認証情報を使ってGoogle Sheets APIのクライアントを作成
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
gspread_client = gspread.authorize(creds)  # gspread用のクライアント

# Discord Botの設定
TOKEN = os.getenv('kani_TOKEN')
CHANNEL_ID = int(os.getenv('channel_id_kani'))

# Google Sheetsの情報
SPREADSHEET_ID = os.getenv('spreadsheet_id')
SHEET_NAME = os.getenv('sheet_name')

# データの最後の行を記録するための変数
last_row = 0

# Discord Botクラス
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

        # Botが準備完了後、シートの監視を開始する
        await self.check_for_updates()

    async def check_for_updates(self):
        global last_row

        while True:
            # シートのデータを取得
            sheet = gspread_client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)  # gspread_clientを使用
            data = sheet.get_all_values()

            # 新しい行が追加されているかを確認
            if len(data) > last_row:
                new_row = data[-1]  # 最後の行を取得
                last_row = len(data)

                # 埋め込みメッセージの作成
                embed = discord.Embed(
                    title="匿名意見箱に新しいデータが追加されました！",
                    color=discord.Colour.purple()
                )
                embed.add_field(name="", value=str(new_row), inline=False)

                # 特定のチャンネルに通知を送信
                channel = self.get_channel(CHANNEL_ID)
                await channel.send(embed=embed)

            # 30秒ごとにチェック
            await asyncio.sleep(30)

# Botの実行
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(TOKEN)
