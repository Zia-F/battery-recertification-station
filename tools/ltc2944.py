from smbus2 import SMBus
from global_consts import Consts
import time

# Registers
STATUS_REG                      = 0x00
CONTROL_REG                     = 0x01
ACCUM_CHARGE_MSB_REG            = 0x02
ACCUM_CHARGE_LSB_REG            = 0x03
CHARGE_THRESH_HIGH_MSB_REG      = 0x04
CHARGE_THRESH_HIGH_LSB_REG      = 0x05
CHARGE_THRESH_LOW_MSB_REG       = 0x06
CHARGE_THRESH_LOW_LSB_REG       = 0x07
VOLTAGE_MSB_REG                 = 0x08
VOLTAGE_LSB_REG                 = 0x09
VOLTAGE_THRESH_HIGH_MSB_REG     = 0x0A
VOLTAGE_THRESH_HIGH_LSB_REG     = 0x0B
VOLTAGE_THRESH_LOW_MSB_REG      = 0x0C
VOLTAGE_THRESH_LOW_LSB_REG      = 0x0D
CURRENT_MSB_REG                 = 0x0E
CURRENT_LSB_REG                 = 0x0F
CURRENT_THRESH_HIGH_MSB_REG     = 0x10
CURRENT_THRESH_HIGH_LSB_REG     = 0x11
CURRENT_THRESH_LOW_MSB_REG      = 0x12
CURRENT_THRESH_LOW_LSB_REG      = 0x13
TEMPERATURE_MSB_REG             = 0x14
TEMPERATURE_LSB_REG             = 0x15
TEMPERATURE_THRESH_HIGH_REG     = 0x16
TEMPERATURE_THRESH_LOW_REG      = 0x17

# Command Codes
AUTOMATIC_MODE          = 0xC0
SCAN_MODE               = 0x80
MANUAL_MODE             = 0x40
SLEEP_MODE              = 0x00
PRESCALAR_M_1           = 0x00
PRESCALAR_M_4           = 0x08
PRESCALAR_M_16          = 0x10
PRESCALAR_M_64          = 0x18
PRESCALAR_M_256         = 0x20
PRESCALAR_M_1024        = 0x28
PRESCALAR_M_4096        = 0x30
PRESCALAR_M_4096_2      = 0x31
ALERT_MODE              = 0x04
CHARGE_COMPLETE_MODE    = 0x02
DISABLE_ALCC_PIN        = 0x00
SHUTDOWN_MODE           = 0x01

# Conversion Constants
CHARGE_lsb              = 0.34E-3
VOLTAGE_lsb             = 1.068E-3
CURRENT_lsb             = 29.3E-6
TEMPERATURE_lsb         = 0.25
FULLSCALE_VOLTAGE       = 70
FULLSCALE_CURRENT       = 60E-3
FULLSCALE_TEMPERATURE   = 510

# Charge register reset value
CHARGE_REG_INIT_VAL     = 0x7FFF
CHARGE_REG_INIT_VAL_MSB = 0x7F
CHARGE_REG_INIT_VAL_LSB = 0xFF


###########################################
# LTC2944 Class
# Responsible for:
#   - Reading and writing to LTC2944 chip 
###########################################
class LTC2944:
    def __init__(self, channel):
        self.channel = channel
        self.ltc_bus = SMBus(Consts.BUS)

        self._select_channel()
        LTC2944_mode = AUTOMATIC_MODE | PRESCALAR_M_1024 | DISABLE_ALCC_PIN
        self.ltc_bus.write_byte_data(Consts.LTC_I2C_ADDRESS, CONTROL_REG, LTC2944_mode)

    def __del__(self):
        self.close()

    def close(self):
        self.ltc_bus.close()

    def read_battery_voltage(self):
        self._select_channel()
        voltage_adc_msb = self.ltc_bus.read_byte_data(Consts.LTC_I2C_ADDRESS, VOLTAGE_MSB_REG)
        voltage_adc_lsb = self.ltc_bus.read_byte_data(Consts.LTC_I2C_ADDRESS, VOLTAGE_LSB_REG)

        voltage_adc = voltage_adc_msb << 8 | voltage_adc_lsb
        voltage = (voltage_adc/(65535))*FULLSCALE_VOLTAGE

        return round(voltage, 3)

    def get_mAh_charge(self):
        RESISTOR = 0.01
        PRESCALAR = 1024

        self._select_channel()
        mAh_charge_adc_msb = self.ltc_bus.read_byte_data(Consts.LTC_I2C_ADDRESS, ACCUM_CHARGE_MSB_REG)
        mAh_charge_adc_lsb = self.ltc_bus.read_byte_data(Consts.LTC_I2C_ADDRESS, ACCUM_CHARGE_LSB_REG)

        mAh_charge_adc = (mAh_charge_adc_msb << 8 | mAh_charge_adc_lsb) -  CHARGE_REG_INIT_VAL
        mAh_charge = 1000 * (mAh_charge_adc * CHARGE_lsb * PRESCALAR * 50E-3) / (RESISTOR * 4096)
        return round(mAh_charge, 2)

    def reset_coulomb_counter(self):
        self._select_channel()
        self.ltc_bus.write_byte_data(Consts.LTC_I2C_ADDRESS, ACCUM_CHARGE_MSB_REG, CHARGE_REG_INIT_VAL_MSB)
        self.ltc_bus.write_byte_data(Consts.LTC_I2C_ADDRESS, ACCUM_CHARGE_LSB_REG, CHARGE_REG_INIT_VAL_LSB)

    def _select_channel(self):
        self.ltc_bus.write_byte(Consts.TCA_I2C_ADDRESS, 1 << self.channel)
        time.sleep(0.1)