from tools.logger import Logger, Type
import os
import json
import traceback

##########################################
# Shared constants between multiple files
##########################################
class Consts:
    BUS = 0
    LTC_I2C_ADDRESS = 0x64
    TCA_I2C_ADDRESS = 0x70


##########################################
# User Configs
##########################################
class Config:
    CONFIG_FILE = 'config.json'
    UPDATE_TIME_KEY = 'update_time'
    MAX_VOLTAGE_KEY = 'max_voltage'
    PARTIAL_VOLTAGE_KEY = 'partial_voltage'
    MIN_VOLTAGE_KEY = 'min_voltage'
    MAX_CHARGE_TIME_KEY = 'max_charge_time'
    MAX_DISCHARGE_TIME_KEY = 'max_discharge_time'
    LOGS_FOLDER_KEY = 'logs_folder'
    REPORTS_FOLDER_KEY = 'reports_folder'

    DEFAULT_CONFIG = {
            UPDATE_TIME_KEY: 5,

            MAX_VOLTAGE_KEY: 29.6,
            PARTIAL_VOLTAGE_KEY: 28.3,
            MIN_VOLTAGE_KEY: 22,
            MAX_CHARGE_TIME_KEY: 28800,     # 8hrs
            MAX_DISCHARGE_TIME_KEY: 19800,  # 5.5hrs

            LOGS_FOLDER_KEY: '~/Logs',
            REPORTS_FOLDER_KEY: '~/Reports',
        }

    config = DEFAULT_CONFIG

    def load_config():
        global config
        try:
            if os.path.exists(Config.CONFIG_FILE) and os.path.getsize(Config.CONFIG_FILE) > 0:
                with open(Config.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            else:
                config = Config.DEFAULT_CONFIG
            Logger.get_sys_logger().log(Type.GENERAL, "Config Loaded")
        except:
            config = Config.DEFAULT_CONFIG
            Logger.get_sys_logger().log(Type.ERROR, f"ERROR LOADING CONFIG: {traceback.format_exc()}")

    def save_config():
        try:
            with open(Config.CONFIG_FILE, "w") as f:
                json.dump(config, f)
            Logger.get_sys_logger().log(Type.GENERAL, "Config Saved")
        except:
            Logger.get_sys_logger().log(Type.ERROR, f"ERROR SAVING CONFIG: {traceback.format_exc()}")
        
    def restore_config():
        global config
        try:
            if os.path.exists(Config.CONFIG_FILE):
                os.remove(Config.CONFIG_FILE)
            config = Config.DEFAULT_CONFIG
            Logger.get_sys_logger().log(Type.GENERAL, "Config Restored")
        except:
            config = Config.DEFAULT_CONFIG
            Logger.get_sys_logger().log(Type.ERROR, f"ERROR RESTORING CONFIG: {traceback.format_exc()}")

