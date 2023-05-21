from global_consts import Config
import os
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")

        general_gbox = QGroupBox("General")
        general_gbox_layout = QFormLayout(self)
        general_gbox.setLayout(general_gbox_layout)

        self.update_time = QDoubleSpinBox(self)
        self.update_time.setRange(0, 3600)
        general_gbox_layout.addRow("Update Time (s):", self.update_time)


        thresholds_gbox = QGroupBox("Thresholds")
        threshold_gbox_layout = QFormLayout(self)
        thresholds_gbox.setLayout(threshold_gbox_layout)

        self.max_voltage = QDoubleSpinBox(self)
        self.partial_voltage = QDoubleSpinBox(self)
        self.min_voltage = QDoubleSpinBox(self)
        self.max_charge_time = QSpinBox(self)
        self.max_discharge_time = QSpinBox(self)
        self.max_charge_time.setRange(0, 86400)
        self.max_discharge_time.setRange(0, 86400)
        threshold_gbox_layout.addRow("Max Voltage:", self.max_voltage)
        threshold_gbox_layout.addRow("Partial Voltage:", self.partial_voltage)
        threshold_gbox_layout.addRow("Min Voltage:", self.min_voltage)
        threshold_gbox_layout.addRow("Max Charge Time (s):", self.max_charge_time)
        threshold_gbox_layout.addRow("Max Discharge Time (s):", self.max_discharge_time)


        paths_gbox = QGroupBox("Folder Paths")
        paths_gbox_layout = QFormLayout(self)
        paths_gbox.setLayout(paths_gbox_layout)

        self.logs_folder = QLineEdit(self)
        paths_gbox_layout.addRow("Logs Folder:", self.logs_folder)
        paths_gbox_layout.addWidget(QLabel("*Requires Restart"))
        self.reports_folder = QLineEdit(self)
        paths_gbox_layout.addRow("Reports Folder:", self.reports_folder)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults, self);
        
        layout = QFormLayout(self)
        layout.addWidget(general_gbox)
        layout.addWidget(paths_gbox)
        layout.addWidget(thresholds_gbox)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore)

        self.set_values(Config.config)

    def set_values(self, config):
        self.update_time.setValue(config[Config.UPDATE_TIME_KEY])
        self.logs_folder.setText(config[Config.LOGS_FOLDER_KEY])
        self.reports_folder.setText(config[Config.REPORTS_FOLDER_KEY])
        self.max_voltage.setValue(config[Config.MAX_VOLTAGE_KEY])
        self.partial_voltage.setValue(config[Config.PARTIAL_VOLTAGE_KEY])
        self.min_voltage.setValue(config[Config.MIN_VOLTAGE_KEY])
        self.max_charge_time.setValue(config[Config.MAX_CHARGE_TIME_KEY])
        self.max_discharge_time.setValue(config[Config.MAX_DISCHARGE_TIME_KEY])
    
    def accept(self):
        logs_path = self.logs_folder.text()
        reports_path = self.reports_folder.text()

        if self._check_path(logs_path):
            return
        if self._check_path(reports_path):
            return

        # Inform user that a restart is required if the logs folder was changed
        if logs_path != Config.config[Config.LOGS_FOLDER_KEY]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Restart Required")
            msg.setText(f"The logs folder path was changed. \r\n\r\n Please restart the program for the change to take effect.")
            msg.exec_()

        # Inform user to sync new reports folder with Google Drive
        if reports_path != Config.config[Config.REPORTS_FOLDER_KEY]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Sync Reports Folder")
            msg.setText(f"The reports folder path was changed. \r\n\r\n Please ensure the new folder is synced with Google Drive.")
            msg.exec_()

        Config.config[Config.UPDATE_TIME_KEY]           = self.update_time.value()
        Config.config[Config.MAX_VOLTAGE_KEY]           = self.max_voltage.value()
        Config.config[Config.PARTIAL_VOLTAGE_KEY]       = self.partial_voltage.value()
        Config.config[Config.MIN_VOLTAGE_KEY]           = self.min_voltage.value()
        Config.config[Config.MAX_CHARGE_TIME_KEY]       = self.max_charge_time.value()
        Config.config[Config.MAX_DISCHARGE_TIME_KEY]    = self.max_discharge_time.value()
        Config.config[Config.LOGS_FOLDER_KEY]           = logs_path
        Config.config[Config.REPORTS_FOLDER_KEY]        = reports_path
        Config.save_config()
        super().accept()

    def _check_path(self, path):
        try:
            os.makedirs(os.path.expanduser(path), exist_ok=True)
        except:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Folder Path Error")
            msg.setText(f"Unable to create folder at '{path}'.")
            msg.exec_()
            return True
        return False

    def restore(self):
        self.set_values(Config.DEFAULT_CONFIG)