import serial
import pynmea2
import time
import math
from datetime import datetime

# 前回のデータを保持するためのグローバル変数
last_lat = None
last_lon = None
last_time = None

def haversine(lat1, lon1, lat2, lon2):
    """
    2点間の緯度経度から距離(m)を計算する
    """
    R = 6371000  # 地球の半径 (m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_data(speed_calc_interval, port, baud):
    """
    maincloud.pyのメインループから呼ばれる関数
    """
 
    global last_lat, last_lon, last_time
  
    # 1. 現在のGPS情報を取得
    curr_lat, curr_lon, sat_num, gps_time = get_raw_gps_data(port, baud)
    
    # ⚠️ 修正ポイント1: データが不完全（パースエラーや未測位）なら None を返して上位に任せる
    #if gps_time is None or isinstance(gps_time, (int, float)) or sat_num == -999:
    #    return None  

    curr_time = time.time()
    speed = 0.0
    #print(f"現在の衛星数: {sat_num}")    

    # 2. 速度計算
    if last_lat is not None and last_lon is not None and sat_num is not None:
        time_diff = curr_time - last_time
        
        if time_diff >= speed_calc_interval and last_lat>0 and last_lon >0 and curr_lat>0 and curr_lat>0:
            distance = haversine(last_lat, last_lon, curr_lat, curr_lon)
            speed = distance / time_diff
            last_lat, last_lon, last_time = curr_lat, curr_lon, curr_time
    else:
        # 初回実行時
        last_lat, last_lon, last_time = curr_lat, curr_lon, curr_time
    #print(curr_lat, curr_lon, sat_num, speed, gps_time)
    return curr_lat, curr_lon, sat_num, speed, gps_time


def get_raw_gps_data(port, baud):
    lat = lon = sat_num = gps_time = None

    try:
        # タイムアウトを少し長め（1秒）に設定してデータを待ちやすくします
        with serial.Serial(port, baudrate=baud, timeout=1.0) as ser:
            print(f"{port} を開きました。GPSデータを読み込んでいます...")

            # 3〜5回ほど読み込んでデータが揃わなければ一旦抜ける（無限ループ化の防止）
            for _ in range(20):
                line = ser.readline().decode('ascii', errors='replace')
                
                if line.startswith('$') and ('GGA' in line or 'RMC' in line):
                    try:
                        msg = pynmea2.parse(line)
                        
                            # RMCセンテンスの処理
                        if 'RMC' in line:
                            if hasattr(msg, 'datestamp') and msg.datestamp and msg.timestamp:
                                gps_time = datetime.combine(msg.datestamp, msg.timestamp)
                            
                            # 【追加】RMCからも緯度経度を取得（未測位でなければ）
                            if hasattr(msg, 'latitude') and msg.latitude != 0.0:
                                lat = msg.latitude
                                lon = msg.longitude

                        # GGAセンテンスの処理
                        if 'GGA' in line:
                            if hasattr(msg, 'latitude') and msg.latitude != 0.0:
                                lat = msg.latitude
                                lon = msg.longitude
                                sat_num = msg.num_sats                                    
                                # 全ての情報が揃ったらリターン
                        if lat is not None and lon is not None and gps_time is not None and sat_num is not None:
                           return lat, lon, sat_num, gps_time

                    except pynmea2.ParseError:
                        # パースエラー時は不正値としてNoneを返す
                        return 0, 0, 0, 0

    except serial.SerialException as e:
        print(f"シリアルポートエラー: {e}")
        # ⚠️ 修正ポイント2: ループ外の continue を削除し、安全にNoneを返す
        return 0, 0, 0, 0
    
    # データが揃わなかった場合
    return 0, 0, 0, 0