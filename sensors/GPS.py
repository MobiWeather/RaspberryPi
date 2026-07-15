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
    
    # そもそも有効なGPSデータが取れていなければ、速度0で座標0を返す
    if curr_lat == 0 and curr_lon == 0:
        return curr_lat, curr_lon, sat_num, 0.0, gps_time

    curr_time = time.time()
    speed = 0.0

    # 2. 速度計算
    if last_lat is not None and last_lon is not None and last_time is not None:
        time_diff = curr_time - last_time
        
        # タイポ修正 ＆ 0チェックを有効な値(!=0)に変更
        if time_diff >= speed_calc_interval and last_lat != 0 and last_lon != 0 and curr_lat != 0 and curr_lon != 0:
            distance = haversine(last_lat, last_lon, curr_lat, curr_lon)
            speed = distance / time_diff
            
            # 【重要】計算に成功した時だけ「前回時間」を更新する、
            # または毎回更新するかは「現在の取得方法」に依存しますが、
            # ポートを毎回開け閉めする現環境では、データが取れたら毎回更新が安全です。
            last_lat, last_lon, last_time = curr_lat, curr_lon, curr_time
        else:
            # 指定時間未満の場合は、速度は計算しないが、座標のベースだけ最新に追従させる
            # (これを行わないと、古い座標と一瞬で比較されて速度が跳ね上がるか0になります)
            if time_diff >= speed_calc_interval:
                last_lat, last_lon, last_time = curr_lat, curr_lon, curr_time
    else:
        # 初回実行時
        last_lat, last_lon, last_time = curr_lat, curr_lon, curr_time

    return curr_lat, curr_lon, sat_num, speed, gps_time

def get_raw_gps_data(port, baud):
    # ループに入る前にすべての変数を None で初期化
    lat = None
    lon = None
    gps_time = None
    sat_num = None

    try:
        with serial.Serial(port, baudrate=baud, timeout=1.0) as ser:
            # 必要な情報がすべて揃うまで、または最大100行（十分な行数）読み込む
            # ※20行だとRMCとGGAが揃う前に上限に達してしまうリスクがあります
            for _ in range(1000):
                try:
                    line = ser.readline().decode('ascii', errors='replace').strip()
                except Exception:
                    continue
                
                # プレフィックスに依存しないよう、GGA か RMC を含む行を処理
                if line.startswith('$') and ('GGA' in line or 'RMC' in line):
                    try:
                        msg = pynmea2.parse(line)
                        
                        # 1. RMCセンテンスの処理 (主に時刻、位置の取得)
                        if 'RMC' in line:
                            if hasattr(msg, 'datestamp') and msg.datestamp and msg.timestamp:
                                gps_time = datetime.combine(msg.datestamp, msg.timestamp)
                            
                            if hasattr(msg, 'latitude') and msg.latitude != 0.0:
                                lat = msg.latitude
                                lon = msg.longitude

                        # 2. GGAセンテンスの処理 (位置、衛星数の取得)
                        elif 'GGA' in line:
                            if hasattr(msg, 'latitude') and msg.latitude != 0.0:
                                lat = msg.latitude
                                lon = msg.longitude
                            # 衛星数はGGAからのみ取得
                            if hasattr(msg, 'num_sats') and msg.num_sats is not None:
                                # pynmea2のnum_satsは文字列で返ることがあるため、念のため数値化
                                sat_num = int(msg.num_sats)
                        
                        # 3. すべての変数が「Noneではない（しっかり上書きされた）」状態になったらリターン
                        if lat is not None and lon is not None and gps_time is not None and sat_num is not None:
                            if lat!=0 and lon!=0 and sat_num!=0:
                                return lat, lon, sat_num, gps_time

                    except pynmea2.ParseError:
                        continue # エラー時は次の行を試す

            # ループ上限まで回っても揃わなかった場合、そこまでで取れた値（またはデフォルト値）を返す
            # 常に 0 になるのを防ぐため、取れたものだけを入れて返す
            return lat or 0.0, lon or 0.0, sat_num or 0, gps_time or datetime.now()

    except serial.SerialException as e:
        print(f"シリアルポートエラー: {e}")
        return 0.0, 0.0, 0, datetime.now()
def get_raw_gps_data_(port, baud):
    lat = lon = sat_num = gps_time = None

    try:
        with serial.Serial(port, baudrate=baud, timeout=1.0) as ser:
            # 20行読み込んでデータを探す
            for _ in range(100):
                try:
                    line = ser.readline().decode('ascii', errors='replace')
                except Exception:
                    continue
                
                if line.startswith('$') and ('GGA' in line or 'RMC' in line):
                    try:
                        msg = pynmea2.parse(line)
                        
                        # RMCセンテンスの処理
                        if 'RMC' in line:
                            if hasattr(msg, 'datestamp') and msg.datestamp and msg.timestamp:
                                gps_time = datetime.combine(msg.datestamp, msg.timestamp)
                            
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
                        continue # エラー時は次の行を試す（即終了させない）

    except serial.SerialException as e:
        print(f"シリアルポートエラー: {e}")
        return 0, 0, 0, 0
    
    # ループ内で揃わなかった場合
    return (lat if lat else 0), (lon if lon else 0), (sat_num if sat_num else 0), gps_time
