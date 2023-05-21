from tools.logger import Logger, Type, State, Action, Warning
from tools.ltc2944 import LTC2944
from ui.plot_window import PlotWindow
from ui.report_pdf import PDF
from datetime import datetime, timedelta
from global_consts import Config
import Odroid.GPIO as GPIO
import matplotlib.pyplot as plt
import matplotlib.transforms as mt
import time
import os
import traceback

########################################
# Constants
########################################

VOLTAGE_QUEUE_SIZE = 15
CAPACITY_REST_TIME = 120 # 2 mins
REST_TIME_BETWEEN_CHARGE_SWITCH = 0.2

# These need to be properly determined and set
CHARGE_VOLTAGE_SLOPE_THRESHOLD = -1
# Don't think we can use this - voltage goes pretty flat when its charging normally
CHARGE_FLAT_VOLTAGE_SLOPE_ENVELOPE = 0.0005     

# GPIO setup
# GPIO.setwarnings(False)
GPIO.setmode(GPIO.WIRINGPI)

###########################################
# Battery Class
# Responsible for:
#   - Controlling battery and logic
#   - Running tests based on the action set
###########################################
class Battery:
    def __init__(self, serial_num, charge_pin, discharge_pin, led_pin, channel):
        # Store battery parameter and create Logger and LTC objects
        self.serial_num = serial_num
        self.charge_pin = charge_pin
        self.discharge_pin = discharge_pin
        self.led_pin = led_pin
        self.logger = Logger(self.serial_num)
        try:
            self.ltc2944 = LTC2944(channel)
        except:
            self.logger.log(Type.ERROR, "I2C Connection Failed")

        # GPIO setup
        GPIO.setup(self.charge_pin, GPIO.OUT, initial=0)
        GPIO.setup(self.discharge_pin, GPIO.OUT, initial=0)
        GPIO.setup(self.led_pin, GPIO.OUT, initial=0)

        # Initialize variables
        self.voltage_readings = {}      # Stores voltage and reading time history
        self.voltage = -1               # Store last read voltage
        self.accum_charge = -1          # Store the accumulated charge
        self.state = State.RESTING      # Current state of the battery
        self.action = Action.REST       # Current action battery must perform
        self.last_action_time = 0       # Time battery last started resting, charging, or discharging
        self.run_capacity_test = False  # Flag to run capacity test
        self.cap_test_done = False      # Flag that sets to true when cap test is done
        self.capacity = -1              # Battery capacity
        self.warning = Warning.NONE     # Flag used to signal warnings
        self.report_data = {}
        self.report_folder = ""
        self.reset_coulomb_counter()

        self.logger.log(Type.GENERAL, "Connected")

    def __del__(self):
        self.cleanup()
        return

    # Store the current voltage of the battery
    # and update the voltage queue
    def get_voltage(self):
        try:
            self.voltage = self.ltc2944.read_battery_voltage()

            # Update the voltage queue
            self.voltage_readings[round(time.time())] = self.voltage
            if len(self.voltage_readings) > VOLTAGE_QUEUE_SIZE:
                first_key = next(iter(self.voltage_readings))
                self.voltage_readings.pop(first_key)

            self.logger.log(Type.VOLTAGE, self.voltage)
        except:
            self.voltage = -1
            self.logger.log(Type.ERROR, "Could not read Voltage")

    # Get the accumulated charge since last battery rest
    def get_mAh_charge(self):
        try:
            self.accum_charge = self.ltc2944.get_mAh_charge()
            self.logger.log(Type.CHARGE, self.accum_charge)
        except:
            self.accum_charge = -1
            self.logger.log(Type.ERROR, "Could not read accumulated charge")
        return self.accum_charge

    def cleanup(self):
        self._set_state(State.RESTING)
        GPIO.output(self.led_pin, 0)
        self.logger.log(Type.GENERAL, "Disconnected")
        return

    def reset_coulomb_counter(self):
        try:
            self.ltc2944.reset_coulomb_counter()
            self.logger.log(Type.GENERAL, "Coulomb counter reset")
        except:
            self.logger.log(Type.ERROR, "Could not reset coulomb counter")

    # Turn on charger relay, turn off load relay
    # Reset time and voltage variables
    def _start_charging(self):
        self._start_charge_rest()
        time.sleep(REST_TIME_BETWEEN_CHARGE_SWITCH)

        GPIO.output(self.discharge_pin, 0)
        GPIO.output(self.charge_pin, 1)

        self.voltage_readings.clear()
        self.reset_coulomb_counter()
        return

    # Turn on load relay, turn off charger relay
    # Reset time and voltage variables
    def _start_discharging(self):
        self._start_charge_rest()
        time.sleep(REST_TIME_BETWEEN_CHARGE_SWITCH)

        GPIO.output(self.charge_pin, 0)
        GPIO.output(self.discharge_pin, 1)
        self.reset_coulomb_counter()
        return
    
    # Turn off load and charger relays
    # Reset time and voltage variables
    def _start_charge_rest(self):
        GPIO.output(self.charge_pin, 0)
        GPIO.output(self.discharge_pin, 0)
        return

    def _calculate_voltage_slope(self):
        if len(self.voltage_readings) < VOLTAGE_QUEUE_SIZE:
            return None

        xavg = 0
        yavg = 0
        numerator = 0
        denominator = 0
        first_time = next(iter(self.voltage_readings))

        for time, volt in self.voltage_readings.items():
            time = time - first_time   # Normalize time so we don't get huge numbers
            yavg += (volt - yavg) / (time + 1)
            xavg += (time - xavg) / (time + 1)

        for time, volt in self.voltage_readings.items():
            time = time - first_time   # Normalize time so we don't get huge numbers
            numerator = numerator + (time - xavg) * (volt - yavg)
            denominator = denominator + ((time - xavg) * (time - xavg))

        # Calculate slope (dsamples/dx)
        slope = numerator / denominator if denominator != 0 else None;   
        return slope

    # Stop charging battery if:
    #   Max voltage is reached or
    #   Max charge time is reached (timeout) or
    #   Voltage decreases sharply (negative delta V) or
    #   Voltage remains the same over the voltage window size (voltage plateau)
    def check_full_charge_complete(self, voltage):
        voltage_slope = self._calculate_voltage_slope()

        end = self.time_since_last_action() >= Config.config[Config.MAX_CHARGE_TIME_KEY]
        end = end or voltage >= Config.config[Config.MAX_VOLTAGE_KEY]
        if voltage_slope != None:
            end = end or voltage_slope <= CHARGE_VOLTAGE_SLOPE_THRESHOLD
        return end

    # Stop discharging battery if
    #   Max discharge time is reached (timeout) or
    #   Voltage reaches minimum discharge voltage
    def check_full_discharge_complete(self, voltage):
        end = self.time_since_last_action() >= Config.config[Config.MAX_DISCHARGE_TIME_KEY]
        end = end or voltage <= Config.config[Config.MIN_VOLTAGE_KEY]
        return end

    def _on_capacity_test_complete(self):
        self.logger.log(Type.GENERAL, "Capacity Test Done!")
        self.logger.log(Type.GENERAL, f"Capacity = {self.capacity}mAh")
        self.run_capacity_test = False
        self.cap_test_done = True
        GPIO.output(self.led_pin, 1)

        self._generate_capacity_test_report()
        return
    
    def _generate_capacity_test_report(self):
        try:
            # Create Reports folder
            parent_directory = os.path.expanduser(Config.config[Config.REPORTS_FOLDER_KEY])
            file_name = os.path.splitext(self.logger.file_name)[0]
            report_folder = os.path.join(parent_directory, file_name)
            self.report_folder = report_folder
            os.makedirs(report_folder, exist_ok=True)

            # Save Battery logs
            self.logger.save_copy(report_folder)

            # Save Voltage Data
            plot_window = PlotWindow()
            x, y, charge_times, discharge_times, rest_times = self.logger.get_data(Type.VOLTAGE)
            plot_window.set_battery_data(x, y, charge_times, discharge_times, rest_times, Type.VOLTAGE, self.serial_num)
            v_plot_path = plot_window.save_plot(report_folder)
            plot_window.save_csv(report_folder)

            # Save Charge Data
            x, y, charge_times, discharge_times, rest_times = self.logger.get_data(Type.CHARGE)
            plot_window.set_battery_data(x, y, charge_times, discharge_times, rest_times, Type.CHARGE, self.serial_num)
            c_plot_path = plot_window.save_plot(report_folder)
            plot_window.save_csv(report_folder)

            # Save Test Summary PDF
            pdf_path = os.path.join(report_folder, "Capacity_Test_Report.pdf")
            self.report_data['sn'] = self.serial_num
            self.report_data['cap'] = self.capacity

            pdf = PDF(data=self.report_data)
            pdf.add_summary_table()
            pdf.add_plots([v_plot_path, c_plot_path])
            pdf.output(pdf_path, 'F')

            self.logger.log(Type.GENERAL, "Report generated!")
        except:
            self.logger.log(Type.ERROR, f"Unable to generate capacity test report: {traceback.format_exc()}")

    # Set the battery's state (internal function)
    def _set_state(self, state):
        if state == State.RESTING:
            self._start_charge_rest()
        elif state == State.CHARGING:
            self._start_charging()
        elif state == State.DISCHARGING:
            self._start_discharging()

        self.state = state
        self.logger.log(Type.STATUS, state)
        return

    # Set an action for the battery to perform
    def set_action(self, action, internal=False):
        self.action = action
        self.last_action_time = time.time()
        self.logger.log(Type.ACTION, action)

        # Reset cap_test flag if a new action is set by the user and not by us
        if not internal and action is not Action.CAPACITY_TEST:
            self.run_capacity_test = False

    def set_serial_num(self, sn):
        self.logger.log(Type.GENERAL, f"New SN: {sn}")
        self.serial_num = sn
        self.logger.set_id(self.serial_num)
        self.logger.log(Type.GENERAL, f"New SN: {sn}")

    def toggle_do_logs(self):
        # Ensure the log toggle always gets logged
        new_log_state = not self.logger.do_logs
        self.logger.set_do_logs(True)
        self.logger.log(Type.GENERAL, f"Set logging to: {new_log_state}")
        self.logger.set_do_logs(new_log_state)

    def time_since_last_action(self):
        return round(time.time() - self.last_action_time)

    # Update the battery based on its state and the action 
    # it is set to perform
    def update(self):
        self.get_voltage()
        self.get_mAh_charge()
        if self.voltage < 0:
            self.set_action(Action.REST, True)
    
        if self.action == Action.REST:
            self._rest_action_update()
        elif self.action == Action.CHARGE_FULL:
            self._charge_full_action_update()
        elif self.action == Action.CHARGE_PARTIAL:
            self._charge_partial_action_update()
        elif self.action == Action.DISCHARGE_FULL:
            self._discharge_full_action_update()
        elif self.action == Action.DISCHARGE_PARTIAL:
            self._discharge_partial_action_update()
        elif self.action == Action.CAPACITY_TEST:
            self._capacity_test_action_update()

        self.update_warning_flag()
        return

    def update_warning_flag(self):
        WARNING_WAIT_TIME = 30
        time = self.time_since_last_action()

        # Warn if the battery is supposed to be charging or discharging but the accumulated charge is not increasing
        if (self.action == Action.CHARGE_FULL or self.action == Action.CHARGE_PARTIAL) and self.accum_charge == 0 and time > WARNING_WAIT_TIME:
            self.warning = Warning.CHECK_CHARGER
        elif (self.action == Action.DISCHARGE_FULL or self.action == Action.DISCHARGE_PARTIAL) and self.accum_charge == 0 and time > WARNING_WAIT_TIME:
            self.warning = Warning.CHECK_LOAD
        else:
            self.warning = Warning.NONE

    def _capacity_test_action_update(self):
        self.capacity = -1
        self.run_capacity_test = True
        self.cap_test_done = False
        self.report_data = {}
        self.report_data['cf_st'] = datetime.now()
        GPIO.output(self.led_pin, 0)
        self.set_action(Action.CHARGE_FULL, True)

    def _discharge_partial_action_update(self):
        if self.state != State.DISCHARGING:
            self._set_state(State.DISCHARGING)
        if self.voltage <= Config.config[Config.PARTIAL_VOLTAGE_KEY]:
            self.logger.log(Type.GENERAL, f"Partially Discharged in {self.time_since_last_action()}s, {round(self.accum_charge)}mAh")
                
            next_action = Action.REST
            self.set_action(next_action, True)

    def _discharge_full_action_update(self):
        if self.state != State.DISCHARGING:
            self._set_state(State.DISCHARGING)
        if self.check_full_discharge_complete(self.voltage):
            self.logger.log(Type.GENERAL, f"Fully Discharged in {self.time_since_last_action()}s, {round(self.accum_charge)}mAh")

            if self.run_capacity_test:
                self.capacity = abs(self.accum_charge)
                next_action = Action.CHARGE_PARTIAL
                self.report_data['df-cp_t'] = datetime.now()
                self.report_data['df_c'] = round(self.accum_charge)
            else:
                next_action = Action.REST
            self.set_action(next_action, True)

    def _charge_partial_action_update(self):
        if self.state != State.CHARGING:
            self._set_state(State.CHARGING)
        if self.voltage >= Config.config[Config.PARTIAL_VOLTAGE_KEY]:
            self.logger.log(Type.GENERAL, f"Partially Charged in {self.time_since_last_action()}s, {round(self.accum_charge)}mAh")
            if self.run_capacity_test:
                self.report_data['cp_et'] = datetime.now()
                self.report_data['cp_c'] = round(self.accum_charge)
                self._on_capacity_test_complete()

            next_action = Action.REST
            self.set_action(next_action, True)

    def _charge_full_action_update(self):
        if self.state != State.CHARGING:
            self._set_state(State.CHARGING)
        if self.check_full_charge_complete(self.voltage):
            self.logger.log(Type.GENERAL, f"Fully Charged in {self.time_since_last_action()}s, {round(self.accum_charge)}mAh")

            self.report_data['cf_et'] = datetime.now()
            self.report_data['cf_c'] = round(self.accum_charge)
            next_action = Action.REST
            self.set_action(next_action, True)

    def _rest_action_update(self):
        if self.state != State.RESTING:
            self._set_state(State.RESTING)
        if self.run_capacity_test and self.time_since_last_action() >= CAPACITY_REST_TIME:
            self.report_data['df_st'] = datetime.now()
            next_action = Action.DISCHARGE_FULL
            self.set_action(next_action, True)