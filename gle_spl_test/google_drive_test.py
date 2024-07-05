from google.oauth2 import service_account
from googleapiclient.discovery import build

# サービスアカウントの認証情報を設定
credentials = service_account.Credentials.from_service_account_file("just-ratio-368201-5a8966c05bcb.json")
drive_service = build('drive', 'v3', credentials=credentials)

# スプレッドシートID
spreadsheet_id = "1zTjSr9Dvqt5TlCCgLgaTbj-S399BVuHZ"

try:
    # ファイル情報を取得
    file = drive_service.files().get(fileId=spreadsheet_id).execute()
    print(f"ファイル情報: {file}")
except Exception as e:
    print(f"エラーが発生しました: {e}")
