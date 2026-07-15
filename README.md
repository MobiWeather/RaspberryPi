# センサーデータ計測 & クラウド送信システム

本システムは Raspberry Pi などの Linux デバイス上で、GPS・SHT41・大気圧・加速度・カメラなどの各種センサーからデータを取得し、
ローカルへの CSV 保存およびクラウドサービス（Ambient など）への定期送信を行う仕組みです。

---

## 1. 動作環境

以下の環境で動作確認済みです。

- **OS:** Raspberry Pi OS 64-bit（推奨）
- **Python:** `3.10.x` 以上
- **主要パッケージ**
  - `requests`（クラウド API 通信）
  - `libcamera` / `rpicam-apps`（カメラ撮影）
  - 各種 I2C / シリアル通信ライブラリ（センサー用）

---

## 2. GitHub 登録時の注意（重要）

公開リポジトリに登録する際は、以下を **絶対にコミットしないでください**。

- Python 仮想環境フォルダ（`.venv` / `env`）
- 機密情報を含む `.env` ファイル

プロジェクト直下に `.gitignore` を作成し、以下を記述します。

### `.gitignore`（推奨設定）

```text
# Python 仮想環境
.venv/
venv/
env/

# 機密情報
.env

# キャッシュ
__pycache__/
*.pyc

# センサーログ
log/

#ピンの設定

同じセンサーを使う場合、センサーのアドレスが重複するので別busの設定、gpioという好きに使えるピンをSCLやSDAへ切り替える設定が必要

以下のファイルに下記文言を追記する。

sudo nano /boot/firmware/config.txt

dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=13,i2c_gpio_scl=19　この設定の話を取り込んでください

＃可視化ツールについて

maincloud_visualization.py
run_mems_visualization.sh

上記ファイルにて
influxDBというDBとそのDBからデータを取得し可視化するGrafanaを採用している。

sensor-monitorフォルダにてdocker-compose.ymlのファイルを再起動時に実行するように設定している。
