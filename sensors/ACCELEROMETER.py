import smbus
import time
import math


def init_bma400(ADDR,bus_number1):
    try:
        bus = smbus.SMBus(bus_number1)

        # ACC_CONFIG0 (0x19) に 0x02 (Normal Mode) を書き込む
        bus.write_byte_data(ADDR, 0x19, 0x02)
        time.sleep(0.1)
        
        # デフォルトのレンジ(±4G)を確認・設定する場合
        # ACC_CONFIG1 (0x1A) のビット6-7がレンジ設定
        # 0x00=2G, 0x01=4G, 0x02=8G, 0x03=16G
        # ここではライブラリのデフォルトに合わせて 4G (0x01 << 6 = 0x40) を設定
        bus.write_byte_data(ADDR, 0x1A, 0x40 | 0x09) # 4G & 200Hz(0x09)
        return bus
        print("BMA400 initialized (Normal Mode / 4G Range)")
    except Exception as e:
        print(f"Initialization failed: {e}")

def get_accel(ADDR,bus_number1):
    
    bus=init_bma400(ADDR,bus_number1)
    # 0x04から6バイト読み込む (X_LSB, X_MSB, Y_LSB, Y_MSB, Z_LSB, Z_MSB)
    if bus is None:
        return 0,0,0
    data = bus.read_i2c_block_data(ADDR, 0x04, 6)
    
    def decode(lsb, msb):
        # C++コードのロジック: (msb * 256) + lsb
        combined = (msb << 8) | lsb
        # 12bit符号付き処理
        if combined > 2047:
            combined -= 4096
        return combined

    # 生データの取得
    x_raw = decode(data[0], data[1])
    y_raw = decode(data[2], data[3])
    z_raw = decode(data[4], data[5])
    
    # G単位への変換 (4Gレンジの場合、1G = 512 LSB)
    # ※2Gなら1024, 4Gなら512, 8Gなら256, 16Gなら128
    scale = 512.0
    
    
    
    try:
        while True:
            
            total_g = math.sqrt(x_raw**2 + y_raw**2 + z_raw**2)/scale
            print(f"現在の重力: {total_g:.2f} G")
            print(f"X: {x_raw/scale:6.3f} G | Y: {y_raw/scale:6.3f} G | Z: {z_raw/scale:6.3f} G")
            
            return x_raw / scale, y_raw / scale, z_raw / scale
           
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0,0,0

