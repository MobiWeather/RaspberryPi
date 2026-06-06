import json
import time
import csv
import os
import threading  # 裏で処理を実行するために追加
from datetime import datetime, timezone
from sensors import GPS,Multiple_SHT41MEMS,ATMOSPRESS,ACCELEROMETER,CAMERA
from visualization import Streamlit
import glob
import requests
import subprocess
import random
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
#起動時に有効（enabled）になっているサービスを一覧表示
#systemctl list-unit-files --type=service | grep enabled  grep mems
#現在バックグラウンドで実際に動いているサービスを確認
#sudo systemctl list-units --type=service --state=running
#有効化状態の確認
#systemctl is-enabled mems.service
#有効
#sudo systemctl enable mems.service
#status
#systemctl status mems.service

# --- InfluxDB 設定 ---
token = "4CPq5Yap8YeXWE2CVcG96sdnJmGg6VWAd6FDT0q7hRW3U5GtLvrK_3O07ptyGkQDVszQeTKlb2ns0xul_pUxbQ=="
org = "MobiWeather"
bucket = "sensor_data"
url = "http://localhost:8086"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


#, sht41_sensor, pressure_sensor, accel_sensor, camera_module
# ==========================================
# ロックファイルの廃棄（クリーンアップ）関数
# ==========================================
def cleanup_lock_files(LOCK_TARGET_DIRS,LOCK_EXTENSIONS):
    
    # libcamera関連のプロセスを強制終了
    subprocess.run(["sudo", "pkill", "-f", "rpicam"], stderr=subprocess.DEVNULL)
    # もし別のPythonスクリプトが掴んでいる場合はそれも終了（自身を除く）
    # ※自身のファイル名が "main.py" の場合は、それ以外のpythonプロセスを落とす
    current_pid = os.getpid()
    print("ロック解除完了。")
    print("=== [STEP 1] 古いロックファイルの廃棄を開始します ===")
    removed_count = 0
#    password = os.environ.get("MY_APP_PASSWORD")
#    if not password:
#        print("エラー: 環境変数 MY_APP_PASSWORD が設定されていません。")
#        exit(1)

#    print("環境変数からパスワードを正常に読み込みました。")
    for target_dir in LOCK_TARGET_DIRS:
        if not os.path.exists(target_dir):
            continue
            
        for ext in LOCK_EXTENSIONS:
            # 検索パスを作成 (例: /tmp/*.lock)
            search_path = os.path.join(target_dir, ext)
            lock_files = glob.glob(search_path)
            
            for file_path in lock_files:
                try:
                    os.remove(file_path)
                    print(f"廃棄成功: {file_path}")
                    removed_count += 1
                except PermissionError:
                    print(f"権限エラー(スキップ): {file_path} (sudoでの実行が必要かもしれません)")
                except Exception as e:
                    print(f"廃棄失敗: {file_path} 原因: {e}")
                    
    print(f"=== クリーンアップ完了（計 {removed_count} 件のロックファイルを廃棄しました） ===\n")

    
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def get_addr(hex_str):
    """JSONの文字列を数値に変換する"""
    return int(hex_str, 16)

def send_to_anbient_worker(payload,API_URL):
    try:
        print(payload)
        print(API_URL)
        
        response = requests.post(API_URL, json=payload, timeout=10)
            # 2. AmbientへPOST送信            
        if response.status_code == 200:
            print(f" データ送信成功: {response.status_code}")
        else:
            print(f" 送信エラー: {response.status_code}, {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"ネットワークエラーが発生しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
    
def main():
    config = load_config()
    v_id = config['vehicle_id']
    sht41_addr_bus1 = hex(get_addr(config['sensors']['bus1']['sht41_addr']))
    accel_addr_bus1 = hex(get_addr(config['sensors']['bus1']['accel_addr']))
    pressure_addr_bus1 = hex(get_addr(config['sensors']['bus1']['pressure_addr']))
    sht41_addr_bus3 = hex(get_addr(config['sensors']['bus3']['sht41_addr']))
  
    bus_number1 = config['sensors']['bus1']['bus_number']
    bus_number3 = config['sensors']['bus3']['bus_number']
    
    GPS_port = config['sensors']['GPS']['port']
    GPS_baud = config['sensors']['GPS']['baud']
    speed_calc_interval = config['sensors']['GPS']['speed_calc_interval']
    
    data_interval = config['sensors']['data_interval']
    
    API_URL=config['cloud']['url']
    WRITE_KEY=config['cloud']['WRITE_KEY']
    data_intervalCloud=config['cloud']['data_interval']
    
    #Lock delete
    LOCK_TARGET_DIRS=config['LOCK_TARGET_DIRS']
    LOCK_EXTENSIONS=config['LOCK_EXTENSIONS']
    
    # 最初にロックファイルを一斉掃除
    cleanup_lock_files(LOCK_TARGET_DIRS,LOCK_EXTENSIONS)
    
    # CSVヘッダーの準備
#     header = [
#         "ID", "dateTime", "lat", "lon", "speed", "satNum",
#         "temp1", "hum1", "dewPoint1", "temp3", "hum3", "dewPoint3",
#         "newhum1", "pressure", "accerateX", "accerateY", "accerateZ", "imageName"
#     ]
#    header = "ID,dateTime,gpsDateTime,lat,lon,speed,satNum,temp1,hum1,dewPoint1,temp3,hum3,dewPoint3,newhum1,pressure,accerateX,accerateY,accerateZ,imageName"
# 
#    header = [
#        "ID", "dateTime","gpsDateTime", "lat", "lon", "speed", "satNum",
#        "temp1", "hum1", "dewPoint1", "temp3", "hum3", "dewPoint3",
#        "newhum1", "pressure",  "imageName"
#    ]
    header = "ID,dateTime,gpsDateTime,lat,lon,speed,satNum,temp1,hum1,dewPoint1,temp3,hum3,dewPoint3,newhum1,pressure,imageName"
    log_dir = config['storage']['csv_path']
    
    os.makedirs(log_dir, exist_ok=True)
    # ファイル名を日時 (yyyyMMddHHmmss.csv) に設定
    file_name =datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + ".csv"
    csv_full_path = os.path.join(log_dir, file_name)

    with open(csv_full_path, 'w') as f:
        f.write(header + "\n")
    
    print(f"Created new file with header: {csv_full_path}")
    
    start_time = time.time()
    start_timeCloud = time.time()
    
    
    try:
        while True:
            now_utc = datetime.now(timezone.utc)
            date_str = now_utc.strftime("%Y/%m/%d/%H:%M:%S")
            folder_name = now_utc.strftime("%Y%m%d")
            
            # --- データ取得 ---
            # GPS & 速度 (speed_calc_intervalを使用)
            #lat, lon, sat_num, speed,gps_time = GPS.get_data(speed_calc_interval,GPS_port,GPS_baud)
            lat, lon, sat_num, speed,gps_time =35.6,140.3,-999,0,now_utc
            #print(f"lat: {repr(lat)} (型: {type(lat)}), lon: {repr(lon)} (型: {type(lon)})")
        
            if gps_time==0 or sat_num==0:
                continue
            
        
            dt_gps_str = gps_time.strftime("%Y/%m/%d/%H:%M:%S")
            #dt_gps_str = "2026-05-18 01:02:03" 
            # 温湿度 (Bus1 & Bus3)
            t1, h1, dp1 = Multiple_SHT41MEMS.get_data(bus_number1)
            t3, h3, dp3 = Multiple_SHT41MEMS.get_data(bus_number3)
            #t3, h3, dp3 =t1, h1, dp1     
            # 新相対湿度の計算 (temp1 と dewpoint3 を使用)
            new_hum1 = Multiple_SHT41MEMS.calculate_new_hum(t1, dp3)
            
            # 大気圧 & 加速度
        
            pres = ATMOSPRESS.get_pressure(bus_number1,int(pressure_addr_bus1,16))
            acc_x, acc_y, acc_z = ACCELEROMETER.get_accel( int(accel_addr_bus1,16),bus_number1)
            
                # フォルダ名を log に変更

            # --- CSV書き出し ---
    #         row = [
    #             v_id, date_str, lat, lon, speed, sat_num,
    #             t1, h1, dp1, t3, h3, dp3,
    #             new_hum1, pres, acc_x, acc_y, acc_z, img_name
    #         ]
            # 1. センサーデータの取得
        
            payload = {
                "writeKey": WRITE_KEY,
                "lat": lat,   # クォーテーションなしの数値
                "lng": lon,  # クォーテーションなしの数値
                "d1": speed,   # 気温
                "d2": t1,   # 湿度
                "d3": h1, # 気圧
                "d4": t3,    # 雨量/感雨
                "d5": h3,    # 風速
                "d6": pres,  # 風向
                "d7": lat,    # その他（日射など）
                "d8": lon   # バッテリー電圧など
            
            }
            
        
            # インターバル調整
            elapsed = time.time() - start_time

            elapsedCloud = time.time() - start_timeCloud
            
            if (elapsed > data_interval and not(lat==0 and lon==0)):
                # 画像撮影
                img_name = CAMERA.get_images(config['storage']['image_dir']+folder_name)
                row = [v_id, date_str, dt_gps_str,lat, lon, speed, sat_num,t1, h1, dp1, t3, h3, dp3,new_hum1, pres,img_name]

                with open(csv_full_path, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
                    
                start_time=time.time()
                # ーーー InfluxDBへの送信処理 ーーー
                point = Point("environment") \
                    .tag("device", "raspberry_pi") \
                    .field("temperature", float(t1)) \
                    .field("pressure", float(pres)) \
                    .time(datetime.utcnow(), WritePrecision.NS)
        
                write_api.write(bucket=bucket, org=org, record=point)
                print(f"Data sent: Temp={t1}, Humid={pres}")
        
            if (elapsedCloud > data_intervalCloud and not(lat==0 and lon==0)):
                send_to_anbient_worker(payload,API_URL)
                start_timeCloud=time.time()
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("ユーザーにより停止されました")
    finally:
        client.close()
    
    
if __name__ == "__main__":
    main()