import matplotlib
import os
import traceback
import csv
from ui.mpl_canvas import MplCanvas
from tools.logger import Type, State
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
matplotlib.use('Qt5Agg')

class PlotWindow(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)
        
        self.sc = MplCanvas(self, width=10, height=8, dpi=100)

        toolbar = NavigationToolbar(self.sc, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)
        self.setLayout(layout)

    def set_battery_data(self, x, y, charge_times, discharge_times, rest_times, type, sn):
        self.type = type
        self.batt_sn = sn
        self.x = x
        self.y = y

        TITLE = f'BATTERY {self.type} OVER TIME SN-{self.batt_sn}'
        X_LABEL = 'Time'
        if self.type == Type.VOLTAGE:
            Y_LABEL = str(self.type) + " (V)"
            self.sc.axes.set_ylim([17, 32])
        else:
            Y_LABEL = str(self.type) + " (mAh)"

        # Add the x and y data
        self.sc.remove_all_datasets()
        self.sc.add_dataset(0, self.x, label=X_LABEL)
        self.sc.add_dataset(1, self.y, label=Y_LABEL)
        self.sc.set_title(TITLE)

        # Visual fix
        if self.type == Type.VOLTAGE:
            self.sc.axes.set_ylim([17, 32])

        # Plot status change lines
        trans = matplotlib.transforms.blended_transform_factory(self.sc.axes.transData, self.sc.axes.transAxes)
        self.sc.axes.vlines(x=charge_times,ymin=0,ymax=1,label=State.CHARGING,lw=1,color='green',transform=trans)
        self.sc.axes.vlines(x=discharge_times,ymin=0,ymax=1,label=State.DISCHARGING,lw=1,color='red',transform=trans)
        self.sc.axes.vlines(x=rest_times,ymin=0,ymax=1,label=State.RESTING,lw=0.5,color='orange',transform=trans)

        # Shrink current axis's height by 10% on the bottom 
        box = self.sc.axes.get_position()
        self.sc.axes.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])

        # Put a legend below current axis
        self.sc.axes.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                fancybox=True, shadow=True, ncol=5)
        
    def save_plot(self, path):
        try:
            file_name = f"TIME_VS_{self.type}_PLOT.png"
            file_path = os.path.join(path, file_name)
            self.sc.fig.savefig(file_path)
        except:
            print(f"ERROR SAVING PLOT: {traceback.format_exc()}")
            return None
        return file_path
    
    def save_csv(self, path):
        try:
            file_name = f"TIME_VS_{self.type}_DATA.csv"
            file_path = os.path.join(path, file_name)

            xlabel = "Time"
            ylabel = "Charge (mAH)" if self.type == Type.CHARGE else "Voltage (V)"
            data = zip(self.x, self.y)

            with open(file_path, 'w') as csvfile:
                filewriter = csv.writer(csvfile)
                filewriter.writerow([xlabel, ylabel])
                filewriter.writerows(data)
        except:
            print(f"ERROR SAVING CSV: {traceback.format_exc()}")
            return None
        return file_path