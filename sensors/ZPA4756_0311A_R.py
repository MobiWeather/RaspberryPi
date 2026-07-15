import smbus
import spidev
import time
class HWInterface:
    def write_reg(self, reg, data):
        raise NotImplementedError
    def read_reg(self, reg):
        raise NotImplementedError
class I2CInterface(HWInterface):
    def __init__(self, bus, dev_addr):
        self.bus = smbus.SMBus(bus)
        self.dev_addr = dev_addr
    def write_reg(self, reg, data):
    
   
        
        self.bus.write_byte_data(self.dev_addr, reg, data)
    def read_reg(self, reg):
        return self.bus.read_byte_data(self.dev_addr, reg)
class SPIInterface(HWInterface):
    def __init__(self, bus, device, max_speed_hz=1000000):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = max_speed_hz
    def write_reg(self, reg, data):
        self.spi.xfer2([reg, data])
    def read_reg(self, reg):
        return self.spi.xfer2([reg | 0x80, 0])[1]
class ZPA4756_0311A_R:
    DEFAULT_ADDR = 0x5c
    def __init__(self, interface):
        self.interface = interface
        self._pressure = 0.0
        self._temperature = 0.0
        self._averages = 0x00
        self._oversampling = 0x05
        self._contentious_mode = False
        self._standby = 0x00
    def begin(self):
        self.interface.write_reg(0x22, 0x04)  # SWリセット
        time.sleep(0.1)
        self.interface.write_reg(0x20, 0x04)  # DEVICE_ENABLE=1
        time.sleep(0.01)
        self.interface.write_reg(0x10, self._averages)
        self.interface.write_reg(0x12, self._standby)
        if self._contentious_mode:
            self.interface.write_reg(0x13, 0x80 | self._oversampling)  # CM=1
            self.interface.write_reg(0x20, 0x06)  # DEVICE_ENABLE=1 ENABLE_MEAS=1
        else:
            self.interface.write_reg(0x13, self._oversampling)  # CM=0
            if self._standby != 0x00:
                self.interface.write_reg(0x20, 0x01)  # ONE-SHOT=1
        return True
    def set_averages(self, averages):
        self._averages = averages
    def set_oversampling_rate(self, osr):
        self._oversampling = osr
    def set_standby_time(self, standby):
        self._standby = standby
    def set_contentious_mode(self, flag):
        self._contentious_mode = flag
    def read_measurements(self, blocking=True):
        if not self._contentious_mode:
            if self._standby == 0x00:
                self.interface.write_reg(0x20, 0x01)  # One-Shotモード開始
                blocking = True
        if blocking:
            cnt = 0
            while True:
                time.sleep(0.002)
                if (self.interface.read_reg(0x27) & 0x03) == 0x03:
                    break
                if cnt >= 750:
                    return False
                cnt += 1
        else:
            if (self.interface.read_reg(0x27) & 0x03) != 0x03:
                return False
        temp_raw_data = self.interface.read_reg(0x2B) | (self.interface.read_reg(0x2C) << 8)
        self._temperature = temp_raw_data * (1.0 / 128.0) - 273.0
        press_raw_data = self.interface.read_reg(0x28) | (self.interface.read_reg(0x29) << 8) | (self.interface.read_reg(0x2A) << 16)
        press_data = press_raw_data
        if press_raw_data & 0x800000:
            press_data -= 0x1000000
        self._pressure = press_data / 64.0
        return True
    def get_pressure(self):
        return self._pressure / 100.0  # Pa -> hPa に変換

    def get_temperature(self):
        return self._temperature