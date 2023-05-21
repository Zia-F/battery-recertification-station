from ui.battery_groupbox import BatteryGroupBox
from ui.settings_window import SettingsWindow
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
import sys
import os
import time

########################################
# Global Variables & Constants
########################################
NUM_BATTS = 3

########################################
# Main Window Subclass
########################################
class MainWindow(QMainWindow):
        def __init__(self):
                super().__init__()
                self.batt_groupbox = []

                top_layout = QVBoxLayout()
                batts_layout = QHBoxLayout()
                toolbar_layout = QGridLayout()
                top_widget = QWidget()
                batts_widget = QWidget()
                toolbar_widget = QWidget()
                
                top_widget.setLayout(top_layout)
                batts_widget.setLayout(batts_layout)
                toolbar_widget.setLayout(toolbar_layout)

                ################ Battery Section ################
                for i in range(NUM_BATTS):
                        self.batt_groupbox.append(BatteryGroupBox(f"Battery {i+1}"))
                        self.batt_groupbox[i].init_components(i)
                        batts_layout.addWidget(self.batt_groupbox[i])

                ################ Bottom Toolbar ################
                exit_butt = QPushButton("Exit")
                restart_butt = QPushButton("Restart")

                exit_butt.clicked.connect(self.exit_click)
                restart_butt.clicked.connect(self.restart_click)

                toolbar_layout.addWidget(restart_butt, 0, 0)
                toolbar_layout.addWidget(exit_butt, 0, 1)


                ################ Top Layer ################
                top_layout.addWidget(batts_widget)
                top_layout.addWidget(toolbar_widget)
                
                ################ Top Toolbar ################
                settings_action = QAction("Settings", self)
                logo_action = QAction(QIcon("ui/assets/z-logo.png"), "Logo", self)
                settings_action.triggered.connect(self.settings_click)
                logo_action.triggered.connect(self.logo_click)
                toolbar = self.addToolBar("Settings")
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                toolbar.setMovable(False)
                toolbar.addAction(settings_action)
                toolbar.addWidget(spacer)
                toolbar.addAction(logo_action)
                toolbar.setContextMenuPolicy(Qt.PreventContextMenu)

                ################ Window Setup ################
                self.setCentralWidget(top_widget)
                self.setWindowIcon(QIcon("assets/logo.png"))
                self.setWindowTitle("Battery Recertification Station")

        def start_threads(self):
                for gb in self.batt_groupbox:
                        gb.update_thread.resume()

        def cleanup(self):
                for gb in self.batt_groupbox:
                        gb.cleanup()

        def settings_click(self):
                self.settings_window = SettingsWindow()
                self.settings_window.exec()
                
        def logo_click(self):
                try:
                        getattr(self, "easter_egg")
                except:
                        self.easter_egg = 0
                try:
                        getattr(self, "easter_egg_t")
                except:
                        self.easter_egg_t = 0

                if time.time() - self.easter_egg_t <= 1:
                        self.easter_egg += 1
                else:
                        self.easter_egg = 0
                self.easter_egg_t = time.time()

                if self.easter_egg == 10:
                        self.easter_egg = 0
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setWindowTitle(f"Easter Egg")
                        msg.setText("Nice, good job!\r\n\r\nNow get back to work.")
                        msg.exec_()

        def exit_click(self):
                self.cleanup()
                qApp.quit()

        def restart_click(self):
                os.execl(sys.executable, sys.executable, *sys.argv)