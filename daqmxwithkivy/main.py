"""
Portions of this code originally authored by: mp-007
Source: https://github.com/mp-007/kivy_matplotlib_widget
"""

# Avoid conflict between mouse provider and touch (very important with touch devices)
from kivy.config import Config

Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from kivy.clock import Clock
from daqmxwithkivy.graph_generator import GraphGenerator
from daqmxwithkivy.daqmx_reader import AnalogInputReader
from multiprocessing import Process, Queue
import numpy as np

# Define the entire UI layout with the KV language
KV = '''
#:import MatplotFigure graph_widget
Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.1
            Button:
                text:"home"
                on_release:app.home()
            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"pan" 
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"zoom box"  
                on_release:
                    app.set_touch_mode('zoombox')
                    self.state='down'   
        BoxLayout:    
            size_hint_y: .7         
            MatplotFigure:
                id:figure_wgt  
        BoxLayout:
            size_hint_y: .3
            GridLayout:
                rows: 1
                cols: 2
                GridLayout:
                    rows: 5
                    cols: 2
                    Label:
                        text: 'CHANNEL SETTINGS'
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'
                        padding_x: 15
                    Label:
                    Label:
                        text: 'Physical Channel'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                    Label:
                        text: 'Max Voltage'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                        input_filter: int
                    Label:
                        text: 'Min Voltage'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                        input_filter: int
                    Label:
                        text: 'Terminal Configuration'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                GridLayout:
                    rows: 4
                    cols: 2
                    Label:
                        text: 'TIMING SETTINGS'
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'
                        padding_x: 15
                    Label:
                    Label:
                        text: 'Sample Clock Source'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                    Label:
                        text: 'Sample Rate'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                        input_filter: int
                    Label:
                        text: 'Number of Samples'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        padding_x: 15
                    TextInput:
                        input_filter: int                    
'''

X = np.linspace(0, 10 * np.pi, 1000)
Y = np.sin(X)


class App(App):
    """
    Main kivy app class
    """

    def build(self):
        """ Kivy method for building the app by returning a widget """
        self.i = 0
        self.screen = Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        """ Called right after build() """
        mygraph = GraphGenerator()
        self.screen.figure_wgt.figure = mygraph.fig
        self.screen.figure_wgt.axes = mygraph.ax1
        self.screen.figure_wgt.xmin = 0
        self.screen.figure_wgt.xmax = 2 * np.pi
        self.screen.figure_wgt.ymin = -1.1
        self.screen.figure_wgt.ymax = 1.1
        self.screen.figure_wgt.line1 = mygraph.line1
        self.home()
        Clock.schedule_interval(self.update_graph, 1 / 60)

        self.ui_queue = Queue()
        self.cmd_queue = Queue()

    def set_touch_mode(self, mode):
        self.screen.figure_wgt.touch_mode = mode

    def home(self):
        self.screen.figure_wgt.home()

    def update_graph(self, _):
        if self.i < 1000000:
            xdata = np.append(self.screen.figure_wgt.line1.get_xdata(), X[self.i])
            self.screen.figure_wgt.line1.set_data(xdata, np.append(self.screen.figure_wgt.line1.get_ydata(), Y[self.i]))
            if self.i > 2:
                self.screen.figure_wgt.xmax = np.max(xdata)
                if self.screen.figure_wgt.axes.get_xlim()[0] == self.screen.figure_wgt.xmin:
                    self.home()
                else:
                    self.screen.figure_wgt.figure.canvas.draw_idle()
                    self.screen.figure_wgt.figure.canvas.flush_events()

            self.i += 1
        else:
            Clock.unschedule(self.update_graph)

    def update_physical_channel(self):
        """ Updates the physical channel to be used for the DAQmx task """

    def update_max_voltage(self):
        """ Updates the max voltage to be used for the DAQmx task """

    def update_min_voltage(self):
        """ Updates the min voltage to be used for the DAQmx task """

    def update_terminal_configuration(self):
        """ Updates the terminal configuration to be used for the DAQmx task """

    def update_sample_clock_source(self):
        """ Updates the sample clock source to be used for the DAQmx task """

    def update_sample_rate(self):
        """ Updates the sample rate to be used for the DAQmx task """

    def update_number_of_samples(self):
        """ Updates the sample rate to be used for the DAQmx task """

if __name__ == "__main__":
    App().run()
