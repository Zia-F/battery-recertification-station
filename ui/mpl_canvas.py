import matplotlib
import traceback
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')

########################################
# Constants
########################################
DATA_KEY = 'data'
DATA_LABEL_KEY = 'datalabel'
ENABLED_KEY = 'enabled'

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.dataset = {}
        self.xdata_id = None
        self.title = ''
        super(MplCanvas, self).__init__(self.fig)


    def add_dataset(self, id, data, label='', enabled=True):
        try:
            self.dataset[id] = {
                DATA_KEY:     data, 
                DATA_LABEL_KEY: label,
                ENABLED_KEY:    enabled}
            self._redraw_canvas()
        except Exception:
            print(traceback.format_exc())
            return True
        return False
    
    def add_datasets(self, ids, data, labels=None, enabled=None):
        try:
            for i in range(len(ids)):
                self.dataset[ids[i]] = {
                    DATA_KEY:       data[i],
                    DATA_LABEL_KEY: '' if labels is None else labels[i],
                    ENABLED_KEY:    True if enabled is None else enabled[i]}
            self._redraw_canvas()
        except Exception:
            print(traceback.format_exc())
            return True
        return False

    def remove_dataset(self, id):
        try:
            del self.dataset[id]
            if id == self.xdata_id:
                self.xdata_id = None
            self._redraw_canvas()
        except Exception:
            print(traceback.format_exc())
            return True
        return False

    def remove_all_datasets(self):
        try:
            self.dataset = {}
        except Exception:
            print(traceback.format_exc())
            return True
        return False

    def set_dataset_visibility(self, id, enabled):
        try:
            self.dataset[id][ENABLED_KEY] = enabled
            self._redraw_canvas()
        except Exception:
            print(traceback.format_exc())
            return True
        return False
    
    def set_title(self, title):
        self.title = title
        self.axes.set_title(title)

    def set_xdata(self, id):
        self.xdata_id = id
        self._redraw_canvas()

    def _redraw_canvas(self):
        try:
            self.axes.cla()

            # Use self.xdata_id as the independent variable if set, 
            # otherwise use the first dataset
            xdata_id = self.xdata_id if self.xdata_id in self.dataset else list(self.dataset.keys())[0]
            xdata = self.dataset[xdata_id]

            for id, data in self.dataset.items():
                if data[ENABLED_KEY] and id != xdata_id:
                    self.axes.plot(xdata[DATA_KEY], data[DATA_KEY], label=data[DATA_LABEL_KEY])
            
            xlabel = xdata[DATA_LABEL_KEY]
            ylabel = 'Value'
            self.axes.set_xlabel(xlabel=xlabel)
            self.axes.set_ylabel(ylabel=ylabel)
            self.axes.legend()
            self.axes.set_title(self.title)
            self.draw()
        except Exception:
            print(traceback.format_exc())
            return True
        return False