import time
import requests
from sensors.ZPA4756_0311A_R import I2CInterface, ZPA4756_0311A_R


def get_pressure(bus_number,device_address):# I2Cインターフェースの初期化

    i2c_interface = I2CInterface(bus_number, device_address)

    # センサーの初期化
    sensor = ZPA4756_0311A_R(i2c_interface)
    sensor.begin()

    while True:
        try:
            
            if sensor.read_measurements(blocking=True):  # 測定が成功した場合
                pressure = sensor.get_pressure()
                temperature = sensor.get_temperature()
                print(f"Pressure: {pressure:.2f} hPa")  # 単位をhPaで表示
                print(f"Temperature: {temperature:.2f} °C")

                return pressure
                # データをアップロード
    #             upload_to_ambient(pressure, temperature)
            else:
                print("Measurement failed!")
                
        except KeyboardInterrupt:
            print("Stopping measurement.")

