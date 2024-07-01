import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets APIの設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("just-ratio-368201-5a8966c05bcb.json", scope)
client = gspread.authorize(creds)
spreadsheet_id = "1zTjSr9Dvqt5TlCCgLgaTbj-S399BVuHZ"

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
    exit()
