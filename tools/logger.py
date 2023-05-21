from enum import Enum
from datetime import datetime
import traceback
import os
import shutil

########################################
# Constants
########################################
SEP = "\t"
MAX_DATA_POINTS = 1000

########################################
# Enums
########################################

# Log Types
class Type(Enum):
    GENERAL = 1
    STATUS = 2
    VOLTAGE = 3
    ERROR = 4
    ACTION = 5
    CHARGE = 6

    def __str__(self):
        return self.name

# Battery States
class State(Enum):
    RESTING = 1
    CHARGING = 2
    DISCHARGING = 3

    def __str__(self):
        return self.name

# Battery Actions
class Action(Enum):
    REST = 1
    CHARGE_FULL = 2
    CHARGE_PARTIAL = 3
    DISCHARGE_FULL = 4
    DISCHARGE_PARTIAL = 5
    CAPACITY_TEST = 6
    RECONDITION = 7 # TODO

    def __str__(self):
        return self.name
    
# Battery Warnings
class Warning(Enum):
    NONE = 1
    CHECK_CHARGER = 2
    CHECK_LOAD = 3

    def __str__(self):
        return self.name
    
    def ui_string(self):
        if self == Warning.CHECK_CHARGER:
            return "Please check charger"
        elif self == Warning.CHECK_LOAD:
            return "Please check load"
        return self.name


###########################################
# Logger Class
# Responsible for:
#   - Creating and appending to log file
#   - Retrieving data from log file
###########################################
class Logger:
    sys_logger = None

    def __init__(self, id, do_logs = True, add_date_to_filename = True):
        self.set_do_logs(do_logs)
        self.set_id(id, add_date_to_filename)

    def log(self, type, msg):
        if not self.do_logs:
            return
        try:
            dt_string = datetime.now().isoformat()
            msg_formatted = f"{dt_string}{SEP}{self.id}{SEP}{type}{SEP}{msg}"
            with open(self.file_path, 'a') as f:
                f.write(msg_formatted + '\n')
            print(msg_formatted)
        except:
            print(f"ERROR LOGGING {traceback.format_exc()}")

    # Parse log file and retrieve the specified data type
    def get_data(self, type, start_time: float = 0, end_time: float = float('inf')):
        time = []
        data = []
        charge_times = []
        discharge_times = []
        rest_times = []

        if type != Type.VOLTAGE and type != Type.CHARGE:
            return time, data, charge_times, discharge_times, rest_times

        try:
            with open(self.file_path, 'r') as f:
                lines = f.readlines()

            # Parse and store time and data values, if within time range
            for line in lines:
                line = line.split(SEP)
                if len(line) > 3: #and int(line[0]) >= start_time and int(line[0]) <= end_time:
                    curr_log_type = line[2]
                    t = datetime.fromisoformat(line[0])
                    if curr_log_type == str(type):
                        value = float(line[3].rstrip())
                        time.append(t)
                        data.append(value)
                        
                    if curr_log_type == str(Type.STATUS):
                        status = State[line[3].rstrip()]
                        if status == State.CHARGING:
                            charge_times.append(t)
                        elif status == State.DISCHARGING:
                            discharge_times.append(t)
                        else:
                            rest_times.append(t)
            
            # Remove excess points - for faster plotting
            num_excess_points = len(time) - MAX_DATA_POINTS
            if num_excess_points > 0:
                for i in range(num_excess_points):
                    del time[i % len(time)]
                    del data[i % len(data)]
        except:
            print(f"ERROR PARSING DATA: {traceback.format_exc()}")
        return time, data, charge_times, discharge_times, rest_times

    def set_id(self, id, add_date_to_filename = True):
        self.id = id

        if add_date_to_filename:
            dt_string = datetime.now().replace(microsecond=0).isoformat()
            self.file_name = f"{self.id}_{dt_string}.log"
        else:
            self.file_name = f"{self.id}.log"

        try:
            # Have to do this import here due to circular dependency issue
            from global_consts import Config
            LOGS_FOLDER = os.path.expanduser(Config.config[Config.LOGS_FOLDER_KEY])
            
            self.file_path = os.path.join(LOGS_FOLDER, self.file_name)     
            os.makedirs(LOGS_FOLDER, exist_ok=True)
        except:
            print(f"ERROR CREATING FOLDER: {traceback.format_exc()}")

    def set_do_logs(self, do_logs):
        self.do_logs = do_logs

    def view(self):
        try:
            if os.path.exists(self.file_path):
                os.system(f"pluma {self.file_path}")
                return False
        except:
            print(f"ERROR OPENING FILE: {traceback.format_exc()}")
        return True

    def delete(self):
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                return False
        except:
            print(f"ERROR DELETING FILE: {traceback.format_exc()}")
        return True
    
    def save_copy(self, new_folder):
        try:
            new_file_path = os.path.join(new_folder, self.file_name)
            shutil.copyfile(self.file_path, new_file_path)
            return False
        except:
            print(f"ERROR COPYING FILE: {traceback.format_exc()}")
        return True
    
    def get_sys_logger():
        if Logger.sys_logger == None:
            Logger.sys_logger = Logger("System", add_date_to_filename=False)
        return Logger.sys_logger