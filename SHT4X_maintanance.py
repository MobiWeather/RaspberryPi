import time
from smbus2 import SMBus, i2c_msg

I2C_BUS = 1
SHT45_ADDR = 0x44
CMD_HEATER_HIGH_1S = 0x39
CMD_MEASURE_HIGH = 0xFD



def read_data(bus, cmd, wait_time):
    # 1. まずコマンド（1バイト）を書き込む
    write_msg = i2c_msg.write(SHT45_ADDR, [cmd])
    bus.i2c_rdwr(write_msg)
    
    # 2. センサー内部の処理（加熱や測定）を待つ
    time.sleep(wait_time)
    
    # 3. 余計なレジスタ番号を送らず、純粋に6バイト読み込む ★ここが重要！
    read_msg = i2c_msg.read(SHT45_ADDR, 6)
    bus.i2c_rdwr(read_msg)
    
    # read_msg.buf からデータを取り出す
    data = list(read_msg)
    
    # 温湿度の換算演算（ここは前と同じです）
    t_ticks = (data[0] << 8) | data[1]
    rh_ticks = (data[3] << 8) | data[4]
    
    temperature = -45 + 175 * (t_ticks / 65535.0)
    humidity = -6 + 125 * (rh_ticks / 65535.0)
    humidity = max(0, min(100, humidity))
    
    return temperature, humidity

with SMBus(I2C_BUS) as bus:
    print("ヒータ機能をONにします (200mW / 1秒間)")
    # ヒータONコマンド時は、加熱時間(1s) + 測定時間(約0.01s) を考慮して少し長めに待つ
    t, rh = read_data(bus, CMD_HEATER_HIGH_1S, wait_time=3.1)
    print(f"加熱中のダミーデータ: {t:.2f}°C / {rh:.2f}%RH")
    
    print("ヒータは自動停止しました。センサーを環境温度になじませるため60秒待機します...")
    time.sleep(60)
    
    print("通常の高精度測定を実行します...")
    t, rh = read_data(bus, CMD_MEASURE_HIGH, wait_time=2)
    print(f"正常な環境データ: {t:.2f}°C / {rh:.2f}%RH")