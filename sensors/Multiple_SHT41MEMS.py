import time
import board
from adafruit_blinka.microcontroller.generic_linux.i2c import I2C as i2c_os
import adafruit_sht4x
import math

def calculate_saturation_vapor_pressure(temp_c):
    """
    指定された式を用いて飽和水蒸気圧(hPa)を計算する
    T: 絶対温度 (K)
    """
    T = temp_c + 273.15  # 摂氏からケルビンへ変換
    
    # ご指定の数式
    ln_ew = (
        -6096.9385 * (T**-1) 
        + 21.2409642 
        - 2.711193e-2 * T 
        + 1.673952e-5 * (T**2) 
        + 2.433502 * math.log(T)
    )
    
    ew = math.exp(ln_ew)  # Pa単位で出力されることが多いため、hPaにする場合は調整が必要
    return ew # Pa単位

def calculate_dewpoint(temp_c, hum_rh):
    """
    気温と相対湿度から、指定式を用いて露点温度を計算する（ニュートン法による近似）
    """
    if temp_c is None or hum_rh <= 0:
        return 0.0
    
    # 現在の水蒸気圧 e を計算
    ew_temp = calculate_saturation_vapor_pressure(temp_c)
    e = ew_temp * (hum_rh / 100.0)
    
    # 露点温度 Td を求める (ew(Td) = e となる Td を探索)
    # 簡易的には元の気温から徐々に下げて収束させる
    #td = temp_c
    #for _ in range(10): # 10回程度のループで十分収束します
    #    ew_td = calculate_saturation_vapor_pressure(td)
        # 傾き（微分係数）を近似的に求めてニュートン法を適用
    #    diff = (calculate_saturation_vapor_pressure(td + 0.01) - ew_td) / 0.01
    #td = td - (ew_td - e) / diff
    # --- ステップ2: y の計算 ---
    # e / 611.213 の自然対数
    y = math.log(e / 611.213)

    # --- ステップ3: td (℃) の計算 ---
    if y >= 0:
        td = (
            13.715 * y 
            + 8.4262e-1 * (y**2)
            + 1.9048e-2 * (y**3)
            + 7.8158e-3 * (y**4)
        )
    else:
        td = (
            13.7204 * y 
            + 7.36631e-1 * (y**2)
            + 3.32136e-2 * (y**3)
            + 7.78591e-4 * (y**4)
        )    
    return round(td, 2)

def calculate_new_hum(temp1, dewpoint3):
    """
    bus3の露点（dewpoint3）から絶対湿度を想定し、
    bus1の気温（temp1）における相対湿度を逆算する
    """
    # 露点温度における飽和水蒸気圧 ＝ 現在の水蒸気圧 e
    e = calculate_saturation_vapor_pressure(dewpoint3)
    # temp1における飽和水蒸気圧
    ew_t1 = calculate_saturation_vapor_pressure(temp1)
    
    # 相対湿度の計算
    new_hum1 = (e / ew_t1) * 100.0
    return round(min(100, max(0, new_hum1)), 2)

def get_data(bus_number):
    """
    指定されたI2Cバス(1 or 3)から温湿度を取得し、露点温度を計算して返す
    """
    while True:
        try:
            # バス3 (GPIO 13, 19)
            try:
                # 自作したラッパー経由でバス3を開く
                i2c_wrapped = I2CBusWrapper(bus_number)
                sensor = adafruit_sht4x.SHT4x(i2c_wrapped)
            except Exception as e:
                print(f"バス3の初期化に失敗しました: {e}")
                return
            
           
            t, h = sensor.measurements

            print(f" (bus number) : {bus_number} / (標準) : {t:.2f} °C / {h:.1f} %")
            print("-" * 50)
        
            # 露点温度の計算
            dewpoint = calculate_dewpoint(t, h)
            return round(t, 2), round(h, 2), dewpoint

        except Exception as e:
            print(f"Error reading SHT41 on bus {bus_number}: {e}")
            # エラー時はNoneまたは0を返してmain側で処理させる
            return -999, -999,-999
    # --- try_lock エラーを回避するためのラッパークラス ---
class I2CBusWrapper:
    def __init__(self, bus_id):
        self._i2c = i2c_os(bus_id)

    def try_lock(self):
        return True

    def unlock(self):
        pass

    def writeto(self, address, buffer, **kwargs):
        return self._i2c.writeto(address, buffer, **kwargs)

    def readfrom_into(self, address, buffer, **kwargs):
        return self._i2c.readfrom_into(address, buffer, **kwargs)

    def writeto_then_readfrom(self, address, out_buffer, in_buffer, **kwargs):
        return self._i2c.writeto_then_readfrom(address, out_buffer, in_buffer, **kwargs)

# --- メイン処理 ---
# def read_sensors():
#     # バス1 (標準)
#     i2c1 = board.I2C()
#     sensor1 = adafruit_sht4x.SHT4x(i2c1)
#     
#     # バス3 (GPIO 13, 19)
#     try:
#         # 自作したラッパー経由でバス3を開く
#         i2c3_wrapped = I2CBusWrapper(3)
#         sensor3 = adafruit_sht4x.SHT4x(i2c3_wrapped)
#     except Exception as e:
#         print(f"バス3の初期化に失敗しました: {e}")
#         return
# 
#     print("計測を開始します...")
#     print("-" * 50)
# 
#     try:
#         while True:
#             t1, h1 = sensor1.measurements
#             t3, h3 = sensor3.measurements
# 
#             print(f"Bus 1 (標準) : {t1:.2f} °C / {h1:.1f} %")
#             print(f"Bus 3 (13/19): {t3:.2f} °C / {h3:.1f} %")
#             print("-" * 50)
#             
#             time.sleep(1)
# 
#     except KeyboardInterrupt:
#         print("\n終了します")

if __name__ == "__main__":
    get_data(bus_number)