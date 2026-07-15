import subprocess
import time
from datetime import datetime
from pathlib import Path

def get_images(save_path, v_id):
    # 1. 保存用フォルダの作成
    save_dir = Path(save_path)
    save_dir.mkdir(exist_ok=True)

    print("--- 10秒おきの撮影を開始します ---")
    
    try:
        while True:
            # 2. 現在時刻をファイル名にする
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = save_dir / f"{v_id}_img_{timestamp}.jpg"
            
            # 3. rpicam-still コマンドの構築
            cmd = [
                "rpicam-still",
                "--nopreview",
                "-t", "1",
                "-o", str(file_path)
            ]
            
            # コマンドの実行
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 保存成功: {file_path.name}")
                # return の代わりに yield を使うことで、ループを殺さずに呼び出し元へ値を返せます
                return f"img_{timestamp}.jpg"
                
            else:
                print(f"エラーが発生しました: {result.stderr}")
                return "Error"
            
            # 4. 次の撮影まで10秒待機（ここが抜けているとフリーズの原因になります）
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n撮影を終了しました。")
