#!/bin/bash

# ログ送信元フォルダー（ラズパイ側）
SRC_DIR_LOG="./data/log/"

# ログ送信先フォルダー（Googleドライブ側のフォルダ名）
DEST_DIR_LOG="gdriv:/MobiFolder/all/logs/"

# 【ポイント】日本時間の今日の深夜 00:00:00 からの経過秒数を計算します
NOW_JST=$(date +%s)
TODAY_JST_START=$(date -d "yesterday 00:00:00" +%s)
SECONDS_SINCE_TODAY=$(( NOW_JST - TODAY_JST_START ))

# rcloneで「今日の深夜0時より前に更新されたファイル」だけをコピー
# 今日更新されている最新のログ（CAR-002*）はスキップされます
/usr/bin/rclone copy "$SRC_DIR_LOG" "$DEST_DIR_LOG" --include "CAR-002*" --max-age "${SECONDS_SINCE_TODAY}s"
# 画像送信元フォルダー（ラズパイ側）
SRC_DIR_IMAGE="./data/images/"

# 画像送信先フォルダー（Googleドライブ側のフォルダ名）
DEST_DIR_IMAGE="gdriv:/MobiFolder/all/images/"

# rcloneでコピーを実行
/usr/bin/rclone copy "$SRC_DIR_IMAGE" "$DEST_DIR_IMAGE" --include "CAR-002*" --max-age "${SECONDS_SINCE_TODAY}s" 

# 必要に応じて、送信完了ログを記録する場合
echo "$(date): Upload completed" >> ./gdrive_upload.log