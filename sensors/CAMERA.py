import subprocess
import time
from datetime import datetime
from pathlib import Path


def get_images(save_path):
    # 1. 保存用フォルダの作成
    # 実行した場所と同じフォルダに 'timelapse_photos' フォルダを作ります
    save_dir = Path(save_path)
    save_dir.mkdir(exist_ok=True)

    print("--- 10秒おきの撮影を開始します ---")
    print("※終了するには Ctrl + C を押してください")

    try:
        while True:
            # 2. 現在時刻をファイル名にする (例: 20231027_153005.jpg)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = save_dir / f"img_{timestamp}.jpg"
            
            # 3. rpicam-still (旧 libcamera-still) コマンドを実行
            # --nopreview: 画面にプレビューを出さない
            # -t 1: 起動後すぐに撮影する
            # -o: 保存先を指定
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
                return f"img_{timestamp}.jpg"
            else:
                print(f"エラーが発生しました: {result.stderr}")
                return "Error"
     

    except KeyboardInterrupt:
        print("\n撮影を終了しました。")
