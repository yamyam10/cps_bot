import os
import gspread
import traceback
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# ====== 環境変数の読み込み ======
SPREADSHEET_ID = os.getenv('spreadsheet_id')
SHEET_NAME = os.getenv('sheet_name')

# Googleサービスアカウントのキー情報（Discord Botと同じ構成）
private_key = os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n")
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

# ====== デバッグ処理 ======
def main():
    try:
        # 環境変数の確認
        if not SPREADSHEET_ID or not SHEET_NAME:
            raise ValueError("spreadsheet_id または sheet_name が .env に設定されていません。")

        print("認証中...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
        gspread_client = gspread.authorize(creds)

        print("スプレッドシートへアクセス中...")
        sheet = gspread_client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

        print("データ取得中...")
        data = sheet.get_all_values()

        print(f"\nデータ取得成功！ 総行数: {len(data)} 行")
        if data:
            print(f"最終行の内容: {data[-1]}")
        else:
            print("シートが空です。")

    except Exception as e:
        print("エラーが発生しました:")
        traceback.print_exc()


if __name__ == '__main__':
    main()
