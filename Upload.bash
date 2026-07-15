#!/bin/bash

# =====================================================================
# 0. パスと時間の定義
# =====================================================================
# ログ送信元とローカルバックアップ（退避先）
SRC_DIR_LOG="./data/log/"
LOCAL_BACKUP_DIR_LOG="./data/log_backup/"

# 画像送信元とローカルバックアップ（退避先）
SRC_DIR_IMAGE="./data/images/"
LOCAL_BACKUP_DIR_IMAGE="./data/images_backup/"

# 送信先（Googleドライブ）
# ※「gdriv:」から「gdrive:」に修正しています
DEST_DIR_LOG="gdriv:/MobiFolder/all/logs/"
DEST_DIR_IMAGE="gdriv:/MobiFolder/all/images/"

# 退避用フォルダがなければ自動作成
mkdir -p "$LOCAL_BACKUP_DIR_LOG"
mkdir -p "$LOCAL_BACKUP_DIR_IMAGE"

# 昨日の深夜 00:00:00 (JST) からの経過秒数
NOW_JST=$(date +%s)
TODAY_JST_START=$(date -d "yesterday 00:00:00" +%s)
SECONDS_SINCE_TODAY=$(( NOW_JST - TODAY_JST_START ))


# =====================================================================
# 1. ログの処理
# =====================================================================
# ① 昨日の深夜0時より前のログファイルをGoogleドライブにコピー
/usr/bin/rclone copy "$SRC_DIR_LOG" "$DEST_DIR_LOG" \
  --include "CAR-002*" \
  --min-age "${SECONDS_SINCE_TODAY}s" \
  --no-traverse \
  --tpslimit 3 \
  --checkers 1 \
  --transfers 1

# ② 【ローカル処理】送信が完了した昨日以前の古いログファイルを、ローカルのバックアップフォルダへ安全に移動
# （mmin または mtime オプションを使用して、昨日以前に更新が止まっているファイルをピンポイントで移動させます）
MINUTES_LIMIT=$(( SECONDS_SINCE_TODAY / 60 ))
find "$SRC_DIR_LOG" -name "CAR-002*" -mmin +"$MINUTES_LIMIT" -exec mv {} "$LOCAL_BACKUP_DIR_LOG" \;


# =====================================================================
# 2. 画像の処理
# =====================================================================
# ① 昨日の深夜0時より前の古い画像をGoogleドライブにコピー
/usr/bin/rclone copy "$SRC_DIR_IMAGE" "$DEST_DIR_IMAGE" \
  --include "CAR-002*" \
  --min-age "${SECONDS_SINCE_TODAY}s" \
  --no-traverse \
  --tpslimit 3 \
  --checkers 1 \
  --transfers 1

# ② 【ローカル処理】送信が完了した昨日以前の古い画像を、ローカルのバックアップフォルダへ移動
# ※ 日付フォルダ（20260714など）の構造ごと移動させるために、一度同名ディレクトリを作成してからファイルを移動します
find "$SRC_DIR_IMAGE" -name "CAR-002*" -mmin +"$MINUTES_LIMIT" | while read -r file; do
    # 送信元ファイルに対応する、バックアップ先フォルダのパスを作成
    relative_path="${file#$SRC_DIR_IMAGE}"
    dest_file_dir="$LOCAL_BACKUP_DIR_IMAGE$(dirname "$relative_path")"
    
    # バックアップ先フォルダを作成してファイルを移動
    mkdir -p "$dest_file_dir"
    mv "$file" "$dest_file_dir/"
done

# 空になった画像フォルダ（日付フォルダ）があれば自動で削除（クリーンアップ）
find "$SRC_DIR_IMAGE" -type d -empty -delete


# =====================================================================
# 3. ログの記録
# =====================================================================
echo "$(date): Upload and backup completed" >> ./gdrive_upload.log