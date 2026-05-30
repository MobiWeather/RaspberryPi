import time
import board
import adafruit_sht4x

i2c = board.I2C()  # uses board.SCL and board.SDA
sht = adafruit_sht4x.SHT4x(i2c)

print("SHT45 接続テスト開始")
while True:
    temperature, relative_humidity = sht.measurements
    print(f"温度: {temperature:.2f} °C / 湿度: {relative_humidity:.2f} %")
    time.sleep(1)