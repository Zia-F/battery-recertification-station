from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def __init__(self, *args, data, **kwargs):
        self.WIDTH = 210
        self.HEIGHT = 297
        self.data = data
        super().__init__(*args, **kwargs)
        
    def header(self):
        self.set_font('Arial', 'I', 11)
        self.cell(self.WIDTH/2-10, 10, f"Battery {self.data['sn']}", 0, 0, 'L')
        self.cell(self.WIDTH/2-10, 10, f"{datetime.today().replace(microsecond=0)}", 0, 0, 'R')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')
        self.image('ui/assets/trexo-logo.png', 10, self.HEIGHT - 20, 20)

    def add_summary_table(self):
        self.add_page()
        self._add_page_title('Battery Capacity Test Report')
        
        # Serial number and capacity text
        self.set_font('Arial', '', 12)
        self.ln()
        self.cell(self.WIDTH - 20, 10, f"Battery Serial Number: {self.data['sn']}", 0, align='C')
        self.ln()
        self.cell(self.WIDTH - 20, 10, f"Battery Capacity: {self.data['cap']} mAh", 0, align='C')
        self.ln(20)

        # Text
        self._set_font(False)
        self.cell(self.WIDTH - 20, 10, f"Table 1 presents an overview of the charging and discharging process executed during the capacity test.", 0, align='LR')
        self.ln(10)

        # Table caption
        self.set_font('Arial', 'I', 9)
        self.cell(self.WIDTH - 20, 10, f"Table 1: Battery {self.data['sn']} charge/discharge process", 0, align='C')
        self.ln()

        # Table Header
        self._set_font(True)
        headers = ["", "Start Time", "End Time", "Duration", "Charge (mAh)"]
        widths = [34, 44, 44, 34, 34]
        for i in range(len(headers)):
            if i == 0:
                self.cell(widths[i], 7, headers[i], 0, 0, 'C')
            else:
                self.cell(widths[i], 7, headers[i], 1, 0, 'C')
        self.ln()

        # Timedeltas
        cf_st = self.data['cf_st'].replace(microsecond=0)
        cf_et = self.data['cf_et'].replace(microsecond=0)
        df_st = self.data['df_st'].replace(microsecond=0)
        df_cp_t = self.data['df-cp_t'].replace(microsecond=0)
        cp_et = self.data['cp_et'].replace(microsecond=0)

        cf_duration = cf_et - cf_st
        df_duration = df_cp_t -df_st
        cp_duration = cp_et - df_cp_t
        total_duration = cp_et - cf_st

        total_charge = self.data['cf_c'] + self.data['df_c'] + self.data['cp_c']

        # Full Charge Row
        self._set_font(True)
        self.cell(widths[0], 6, "Full Charge", 1, 0, 'C')
        self._set_font(False)
        self.cell(widths[1], 6, str(cf_st),  1, 0, 'C')
        self.cell(widths[2], 6, str(cf_et),  1, 0, 'C')
        self.cell(widths[3], 6, str(cf_duration),  1, 0, 'C')
        self.cell(widths[4], 6, str(self.data['cf_c']),  1, 0, 'C')
        self.ln() 

        # Full Discharge Row
        self._set_font(True)
        self.cell(widths[0], 6, "Full Discharge",  1, 0, 'C')
        self._set_font(False)
        self.cell(widths[1], 6, str(df_st),  1, 0, 'C')
        self.cell(widths[2], 6, str(df_cp_t),  1, 0, 'C')
        self.cell(widths[3], 6, str(df_duration),  1, 0, 'C')
        self.cell(widths[4], 6, str(self.data['df_c']),  1, 0, 'C')
        self.ln() 

        # Partial Charge Row
        self._set_font(True)
        self.cell(widths[0], 6, "Partial Charge",  1, 0, 'C')
        self._set_font(False)
        self.cell(widths[1], 6, str(df_cp_t),  1, 0, 'C')
        self.cell(widths[2], 6, str(cp_et),  1, 0, 'C')
        self.cell(widths[3], 6, str(cp_duration),  1, 0, 'C')
        self.cell(widths[4], 6, str(self.data['cp_c']),  1, 0, 'C')
        self.ln() 

        # Total Row
        self._set_font(True)
        self.cell(widths[0], 6, "Total",  1, 0, 'C')
        self._set_font(False)
        self.cell(widths[1], 6, str(cf_st),  1, 0, 'C')
        self.cell(widths[2], 6, str(cp_et),  1, 0, 'C')
        self.cell(widths[3], 6, str(total_duration),  1, 0, 'C')
        self.cell(widths[4], 6, str(total_charge),  1, 0, 'C')
        self.ln() 

    def _set_font(self, bold):
        self.set_font('Arial', 'B' if bold else '', 10)

    def add_plots(self, plots):
        self.add_page()
        self._add_page_title('Plots')
        self.image(plots[0], x=25, y=31, h=self.HEIGHT/2 - 15)
        self.image(plots[1], x=25, y=self.HEIGHT / 2 + 11, h=self.HEIGHT/2 - 15)

    def _add_page_title(self, txt):
        self.set_font('Arial', 'B', 12)
        self.cell(self.WIDTH - 20, 10, txt, 1, align='C')
        self.ln(10)