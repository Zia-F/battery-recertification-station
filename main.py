#!/usr/bin/python3

from tools.logger import Logger, Type
from global_consts import Config
from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys
import traceback
import atexit

def main():
        global window
        try:
                atexit.register(cleanup)
                Logger.get_sys_logger().log(Type.GENERAL, "START")
                Config.load_config()

                app = QApplication(sys.argv)
                window = MainWindow()
                window.show()
                window.start_threads()
                app.exec()
        except Exception:
                handle_error(traceback.format_exc())
        
# Exit program on unexpected error
def handle_error(err):
        Logger.get_sys_logger().log(Type.ERROR, err)
        cleanup()
        quit()

# Cleanup on program exit
def cleanup():
        window.cleanup()
        Logger.get_sys_logger().log(Type.GENERAL, "Objects Cleaned Up")

if __name__ == '__main__':
    main()