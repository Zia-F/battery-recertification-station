from tools.battery import Battery, Action
from smbus2 import SMBus
from tools.logger import Logger, Type, State, Warning
from ui.plot_window import PlotWindow
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from global_consts import Consts, Config
import datetime
import time
import string

########################################
# Global Variables & Constants
########################################

BATT_CHARGE_PINS = [21, 23, 24]
BATT_DISCHARGE_PINS = [22, 26, 27]

LED_PINS = [12, 13, 14]

TCA_RESET_PIN = 6

SAFE_FILE_CHARS = set(string.ascii_letters + string.digits + '~-_.')

########################################
# Update Thread Subclass
########################################
class BattUpdateThread(QThread):
        signal = pyqtSignal()
        paused = True
        def run(self):
                while True:
                        if self.paused:
                                time.sleep(0.1)
                                continue
                        self.signal.emit()
                        time.sleep(Config.config[Config.UPDATE_TIME_KEY])

        def pause(self):
                self.paused = True      # Use mutex here?
        
        def resume(self):
                self.paused = False     # Use mutex here?


########################################
# Battery Group Box Subclass
########################################
class BatteryGroupBox(QGroupBox):
 
        def __init__(self, parent = None):
                QGroupBox.__init__(self, parent)
                self.battery = None
                self.battery_connected = False

        def init_components(self, idx):
                self.idx = idx
                self.display_idx = idx + 1

                vbox = QVBoxLayout()
                self.setLayout(vbox)

                ################ Info Labels ################
                self.sn_label = QLabel()
                self.status_label = QLabel()
                self.action_label = QLabel()
                self.voltage_label = QLabel()
                self.charge_label = QLabel()
                self.capacity_label = QLabel()

                self.sn_label.setAlignment(Qt.AlignCenter)
                self.action_label.setAlignment(Qt.AlignCenter)
                self.status_label.setAlignment(Qt.AlignCenter)
                self.voltage_label.setAlignment(Qt.AlignCenter)
                self.charge_label.setAlignment(Qt.AlignCenter)
                self.capacity_label.setAlignment(Qt.AlignCenter)
                vbox.addWidget(self.sn_label)
                vbox.addWidget(self.action_label)
                vbox.addWidget(self.status_label)
                vbox.addWidget(self.voltage_label)
                vbox.addWidget(self.charge_label)
                vbox.addWidget(self.capacity_label)

                grid = QGridLayout()
                butt_widget = QWidget()
                butt_widget.setLayout(grid)

                ################ Action Buttons ################
                self.cap_test_butt = QPushButton("Run Capacity Test")
                self.rest_butt = QPushButton("Rest")
                self.charge_full_butt = QPushButton("Charge Full")
                self.discharge_full_butt = QPushButton("Discharge Full")
                self.charge_partial_butt = QPushButton("Charge Partial")
                self.discharge_partial_butt = QPushButton("Discharge Partial")

                self.cap_test_butt.clicked.connect(self.on_run_cap_test_action)
                self.rest_butt.clicked.connect(self.on_rest_action)
                self.charge_full_butt.clicked.connect(self.on_charge_full_action)
                self.discharge_full_butt.clicked.connect(self.on_discharge_full_action)
                self.charge_partial_butt.clicked.connect(self.on_charge_partial_action)
                self.discharge_partial_butt.clicked.connect(self.on_discharge_partial_action)

                # Allow buttons to stretch when window size is changed
                self.cap_test_butt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                self.rest_butt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                self.charge_full_butt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                self.discharge_full_butt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                self.charge_partial_butt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                self.discharge_partial_butt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                grid.setRowMinimumHeight(0, 50)         # Increase height of Capacity Test button

                advanced_txt_label= QLabel("Advanced")
                grid.addWidget(self.cap_test_butt, 0, 0, 1, 2)
                grid.addWidget(advanced_txt_label, 2, 0)
                grid.addWidget(self.rest_butt, 3, 0, 1, 2)
                grid.addWidget(self.charge_full_butt, 4, 0)
                grid.addWidget(self.discharge_full_butt, 5, 0)
                grid.addWidget(self.charge_partial_butt, 4, 1)
                grid.addWidget(self.discharge_partial_butt, 5, 1)
                
                vbox.addWidget(butt_widget)

                ################ Info and Warning Labels ################
                self.info_label = QLabel()
                self.warning_label = QLabel()
                self.done_label = QLabel()
                self.info_label.setAlignment(Qt.AlignLeft)
                self.warning_label.setAlignment(Qt.AlignLeft)
                self.done_label.setAlignment(Qt.AlignLeft)
                self.info_label.setVisible(False)
                self.warning_label.setVisible(False)
                self.done_label.setVisible(False)
                self.done_label.linkActivated.connect(self.open_report_window)

                vbox.addWidget(self.info_label)
                vbox.addWidget(self.warning_label)
                vbox.addWidget(self.done_label)

                ################ Start Update Thread ################
                self.start_update_thread()

        def open_report_window(self, linkStr):
                QDesktopServices.openUrl(QUrl(linkStr))

        def start_update_thread(self):
                self.update_thread = BattUpdateThread(self)
                # self.update_thread.setDaemon(True)
                self.update_thread.start()
                self.update_thread.signal.connect(self.update_all)

        # Stub methods for now - WIP
        def on_rest_action(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.set_action(Action.REST)
                self.update_all()

        def on_run_cap_test_action(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.set_action(Action.CAPACITY_TEST)
                self.update_all()


        def on_charge_full_action(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.set_action(Action.CHARGE_FULL)
                self.update_all()


        def on_discharge_full_action(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.set_action(Action.DISCHARGE_FULL)
                self.update_all()


        def on_charge_partial_action(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.set_action(Action.CHARGE_PARTIAL)
                self.update_all()


        def on_discharge_partial_action(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.set_action(Action.DISCHARGE_PARTIAL)
                self.update_all()


        def check_connection(self):
               connected = self.check_i2c_connection()
               self.show_info(f"Battery {self.display_idx} Connected" if connected else f"Battery {self.display_idx} Not Connected")
               return connected

        def get_sn(self):
                old_sn = self.battery.serial_num if self.battery_connected else ""
                sn, status = QInputDialog.getText(self, f"Battery {self.display_idx}: Input SN", f"Enter SN for Battery {self.display_idx}:", text=old_sn)
                if status and not sn:
                        self.show_error("Serial number cannot be empty!")
                        status = False
                elif status and not set(sn) <= SAFE_FILE_CHARS:
                        self.show_error(f"Serial number must only consist of letters, numbers, and following characters: '~-_.'")
                        status = False
                return sn, status 

        def modify_sn(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                
                sn, status = self.get_sn()
                if status and self.check_i2c_connection():
                        self.battery.set_serial_num(sn)
                self.update_all()

        def toggle_logs(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                self.battery.toggle_do_logs()

        # Stub methods - WIP
        def view_logs(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                if self.battery.logger.view():
                        self.show_error("Could not open log file! Please check to make sure it exists.")
        
        def delete_logs(self):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return
                if self.battery.logger.delete():
                        self.show_error("Could not delete log file! Please check to make sure it exists.")
                else:
                        self.show_info("Log file deleted!")

        def plot_data(self, type):
                # Ensure battery is connected
                if self.show_not_connected_error():
                        return

                self.plot_window = PlotWindow()
                x, y, charge_times, discharge_times, rest_times = self.battery.logger.get_data(type)
                self.plot_window.set_battery_data(x, y, charge_times, discharge_times, rest_times, type, self.battery.serial_num)
                self.plot_window.show()

        def quit(self):
                self.cleanup()
                qApp.quit()

        def cleanup(self):
                self.update_thread.terminate()
                if self.battery_connected:
                        self.battery.cleanup()

        def update_button_event(self):
                self.update_all()
                self.show_info("Updated!")

        def update_all(self):
                self.update_thread.pause()

                self.update_battery_object()
                if self.battery_connected:
                        self.battery.update()
                self.update_button_states()
                self.update_labels()

                self.update_thread.resume()

        # Check if battery is connected or not 
        # and create/destroy battery object accordingly
        def update_battery_object(self):
                # Determine if battery is connected (if i2c connection is on)
                batt_connected = self.check_i2c_connection()
                batt_exists = self.battery is not None
                if batt_connected and not batt_exists:  
                    self.on_battery_connection()        # New battery detected: Prompt for SN and create battery object
                elif not batt_connected and batt_exists:   
                    self.on_battery_disconnection()     # Battery disconnected: Delete battery object 

        def on_battery_connection(self):
                Logger.get_sys_logger().log(Type.GENERAL, f"Battery connected at channel {self.idx}")
                sn, status = self.get_sn()
                # Ensure battery did not disconnect while SN is typed in
                if status and self.check_i2c_connection():
                        self.create_battery_object(sn)
                        self.battery_connected = True
                else:
                        Logger.get_sys_logger().log(Type.GENERAL, f"Battery disconnected at channel {self.idx}")

        def on_battery_disconnection(self):
                Logger.get_sys_logger().log(Type.GENERAL, f"Battery disconnected at channel {self.idx}")
                self.battery_connected = False
                self.battery.cleanup()
                self.battery = None

        def update_button_states(self):
                self.rest_butt.setEnabled(self.battery_connected)
                self.charge_full_butt.setEnabled(self.battery_connected)
                self.discharge_full_butt.setEnabled(self.battery_connected)
                self.charge_partial_butt.setEnabled(self.battery_connected)
                self.discharge_partial_butt.setEnabled(self.battery_connected)

                cap_test_butt_text = "Run Capacity Test"
                cap_test_enabled = self.battery_connected
                if self.battery_connected and self.battery.run_capacity_test:
                        cap_test_butt_text = "Running Capacity Test..."
                        cap_test_enabled = False
                        
                self.cap_test_butt.setText(cap_test_butt_text)
                self.cap_test_butt.setEnabled(cap_test_enabled)

        def update_labels(self):
                INVALID = -1
                UNKNOWN = "Unknown"

                status_col = "black"
                connected = self.battery is not None
                if connected:
                        sn = self.battery.serial_num 
                        status = self.battery.state 
                        action = self.battery.action
                        voltage = self.battery.voltage
                        charge = self.battery.accum_charge
                        capacity = self.battery.capacity

                        # Update the info labels                
                        status_col = self.set_info_label(status, self.battery.time_since_last_action())
                        self.set_warning_label(self.battery.warning)

                        self.set_done_label(self.battery.cap_test_done, self.battery.report_folder)
                else:
                        sn = "---"
                        status = "NOT CONNECTED"
                        action = "---"
                        voltage = "---"
                        charge = "---"
                        capacity = "---"

                        self.info_label.setVisible(False)
                        self.warning_label.setVisible(False)
                        self.set_done_label(False, None)

                self.sn_label.setText(sn)
                self.status_label.setText(f"Status: <font color='{status_col}'>{status}</font>")
                self.action_label.setText(f"Action: {action}")
                self.voltage_label.setText(f"Voltage: {UNKNOWN}" if voltage is INVALID else f"Voltage: {voltage} V")
                self.charge_label.setText(f"Charge: {UNKNOWN}" if charge is INVALID else f"Charge: {charge} mAH")
                self.capacity_label.setText(f"Capacity: {UNKNOWN}" if capacity is INVALID else f"Capacity: {capacity} mAH")

        def set_info_label(self, state, last_action_time):
                status_col = "black"
                if state == State.CHARGING:
                        status_col = "green"
                        self.info_label.setText(f"Charge Time: {datetime.timedelta(seconds=last_action_time)}")
                        self.info_label.setVisible(True)
                elif state == State.DISCHARGING:
                        status_col = "orange"
                        self.info_label.setText(f"Discharge Time: {datetime.timedelta(seconds=last_action_time)}")
                        self.info_label.setVisible(True)
                else:
                        self.info_label.setVisible(False)
                return status_col

        def set_warning_label(self, warning):
                if warning != Warning.NONE:
                        self.warning_label.setText(f"<font color='orange'>Warning: {warning.ui_string()}</font>")
                        self.warning_label.setVisible(True)
                else:
                        self.warning_label.setVisible(False)

        def set_done_label(self, visible, link):
                if visible:
                        self.done_label.setText(f"<font color='green'>Capacity test done!</font> <a href={link}>View Report</a>")
                        self.done_label.setVisible(True)
                else:
                        self.done_label.setVisible(False)

        # Check if I2C channel is connected to a device1
        def check_i2c_connection(self):
                try:
                        with SMBus(Consts.BUS) as bus:
                                bus.write_byte(Consts.TCA_I2C_ADDRESS, 1 << self.idx)
                                time.sleep(0.1)
                                # This will return an error if the i2c address is not connected
                                bus.read_byte_data(Consts.LTC_I2C_ADDRESS, 0)    
                                return True
                except Exception:
                        return False

        # Create the battery object
        def create_battery_object(self, sn):
                self.battery = Battery(sn, 
                                        BATT_CHARGE_PINS[self.idx], 
                                        BATT_DISCHARGE_PINS[self.idx],
                                        LED_PINS[self.idx],
                                        self.idx)
                Logger.get_sys_logger().log(Type.GENERAL, f"Battery object created with SN={sn}")

        def show_not_connected_error(self):
                if not self.battery_connected:
                        self.show_error("Battery not connected!")
                        return True
                return False

        def show_error(self, err_msg):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle(f"Battery {self.display_idx} Error")
                msg.setText(err_msg)
                msg.exec_()

        def show_info(self, info_msg):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle(f"Battery {self.display_idx} Info")
                msg.setText(info_msg)
                msg.exec_()

        def contextMenuEvent(self, event):
                menu = QMenu(self)
                menu.addSection(f"Battery {self.display_idx}")

                check_connection_action = menu.addAction("&Check Connection")
                update_action = menu.addAction("&Update")
                modify_sn_action = menu.addAction("&Modify SN")
                check_connection_action.triggered.connect(self.check_connection)
                update_action.triggered.connect(self.update_button_event)
                modify_sn_action.triggered.connect(self.modify_sn)

                modify_sn_action.setEnabled(self.battery_connected)

                menu.addSeparator()

                ################ Battery Actions Submenu ################
                cap_test_butt_text = "&Run Capacity Test"
                cap_test_enabled = self.battery_connected
                if self.battery_connected and self.battery.run_capacity_test:
                        cap_test_butt_text = "Running Capacity Test..."
                        cap_test_enabled = False

                actions_submenu = menu.addMenu("&Actions")
                cap_test_action = actions_submenu.addAction(cap_test_butt_text)
                actions_submenu.addSection("Advanced")
                rest_action = actions_submenu.addAction("&Rest")
                actions_submenu.addSeparator()
                charge_full_action = actions_submenu.addAction("&Charge Full")
                charge_partial_action = actions_submenu.addAction("&Charge Partial")
                actions_submenu.addSeparator()
                discharge_full_action = actions_submenu.addAction("&Discharge Full")
                discharge_partial_action = actions_submenu.addAction("&Discharge Partial")

                rest_action.triggered.connect(self.on_rest_action)
                cap_test_action.triggered.connect(self.on_run_cap_test_action)
                charge_full_action.triggered.connect(self.on_charge_full_action)
                charge_partial_action.triggered.connect(self.on_charge_partial_action)
                discharge_full_action.triggered.connect(self.on_discharge_full_action)
                discharge_partial_action.triggered.connect(self.on_discharge_partial_action)

                actions_submenu.setEnabled(self.battery_connected)
                cap_test_action.setEnabled(cap_test_enabled)

                ################ Log Actions Submenu ################
                log_submenu = menu.addMenu("&Logs")
                logging_toggle = log_submenu.addAction("&Logging")
                view_logs_action = log_submenu.addAction("&View")
                delete_logs_action = log_submenu.addAction("&Delete")

                logging_toggle.setCheckable(True)
                logging_toggle.triggered.connect(self.toggle_logs)
                view_logs_action.triggered.connect(self.view_logs)
                delete_logs_action.triggered.connect(self.delete_logs)

                log_submenu.setEnabled(self.battery_connected)
                if self.battery_connected:
                        logging_toggle.setChecked(self.battery.logger.do_logs)

                ################ Plot Actions Submenu ################
                plot_submenu = menu.addMenu("&Plot")
                plot_voltage_action = plot_submenu.addAction("&Voltage")
                plot_charge_action = plot_submenu.addAction("&Charge")

                plot_voltage_action.triggered.connect(lambda x: self.plot_data(Type.VOLTAGE))
                plot_charge_action.triggered.connect(lambda x: self.plot_data(Type.CHARGE))

                plot_submenu.setEnabled(self.battery_connected)

                menu.addSeparator()

                quit_action = menu.addAction("&Quit")
                quit_action.triggered.connect(self.quit)

                action = menu.exec_(self.mapToGlobal(event.pos()))
