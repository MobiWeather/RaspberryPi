import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)
    
# 設定（元のパスや変数をそのまま引き継ぎます）
config = load_config()
v_id = config['vehicle_id']
CSV_DIR = config['storage']['csv_path']     # CSVがあるフォルダ
IMAGE_DIR = config['storage']['image_dir']  # 画像があるフォルダ

# OAuth用の設定
SCOPES = ['https://www.googleapis.com/auth/drive'] # 必要最小限の書き込み権限
CLIENT_SECRET_FILE = './secret.json'             # ダウンロードしたOAuthクライアントJSON
TOKEN_FILE = './token.json'                             # 自動生成されるトークン保存先
HISTORY_FILE = './csv_history.txt'                      # 履歴ログ
LOG_FOLDER_ID = '12UPyNbmqB9d8XtBCpd9b9yzuCRn-npxg'

# Google Drive API サービスを取得（OAuth認証処理）
def get_gdrive_service():
    creds = None
    # 過去にログインした情報（token.json）があれば読み込む
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # ログイン情報がない、または有効期限が切れている場合
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 初回ログイン時：認証情報ファイルからログイン画面を起動
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            # ローカルサーバーを起動して認証を受け取る（デスクトップ環境を想定）
            creds = flow.run_local_server(port=0)
            
        # 取得した認証情報を保存（次回からは自動ログイン）
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def main():
    # API接続
    service = get_gdrive_service()

    # 履歴の読み込み
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            uploaded_files = set(f.read().splitlines())
    else:
        uploaded_files = set()

    # フォルダ内のCSVをチェック
    for filename in os.listdir(CSV_DIR):
        # CSVかつ車両IDで始まり、未アップロードのもののみ対象
        if filename.endswith('.csv') and filename.startswith(v_id) and filename not in uploaded_files:
            file_path = os.path.join(CSV_DIR, filename)
            
            # Google Driveへアップロード
            file_metadata = {'name': filename, 'parents': [LOG_FOLDER_ID]}
            media = MediaFileUpload(file_path, mimetype='text/csv')
            
            try:
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                
                # 成功したら履歴に追記
                with open(HISTORY_FILE, 'a') as f:
                    f.write(filename + '\n')
                print(f"Uploaded CSV: {filename}")
            except Exception as e:
                print(f"Failed to upload {filename}: {e}")

if __name__ == '__main__':
    main()