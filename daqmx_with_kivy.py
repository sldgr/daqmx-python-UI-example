"""

daqmx_with_kivy.py: This is the main script for the DAQmx with Kivy example app. This is a python take on the
LabVIEW built-in example VI called Voltage - Continuous Input. Like the G-code equivalent, this code features the
ability to configure, start and stop a DAQmx single-channel analog input voltage task. Other features worth
mentioning include:

    1. Use of Kivy, a cross-platform NUI development framework for python allowing easy separation of a UI layout and
    business logic
    2. Real-time, (60+ FPS) graph display with home, zoom, and pan
    3. Automatic logging of acquired data to a .dat file
    4. Use of the python multiprocessing package to separate the Kivy App process from the DAQmx Stream Reader process

For more details, see the README.md

UI Portions of this code (the graph_widget.py and graph_generator.py files) originally authored by: mp-007
Source: https://github.com/mp-007/kivy_matplotlib_widget
"""

from multiprocessing import Queue, Process

import numpy as np
from nidaqmx.constants import TerminalConfiguration

from daqmx_reader import AnalogInputReader

# Global Constants
GLOBAL_STOP = 'S'
""" Define the entire UI layout and event functionality with the KV language. This could also be its own .kv file."""
KV = '''
#:import MatplotFigure graph_widget
Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        padding: [20, 20, 20, 20]
        BoxLayout:
            size_hint_y:0.1
            Button:
                text:"Home"
                on_release:app.home()
            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"Pan" 
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"Box Zoom"  
                on_release:
                    app.set_touch_mode('zoombox')
                    self.state='down'   
            Button:
                text: "Start Acquisition"
                on_release: app.start_acquisition()
            Button:
                text: "Stop Acquisition"
                on_release: app.stop_acquisition()
        BoxLayout:
            size_hint_y: 1
            MatplotFigure:
                id:figure_wgt 
        BoxLayout:
            size_hint_y: .5
            GridLayout:
                rows: 1
                cols: 2
                GridLayout:
                    rows: 6
                    cols: 2
                    Label:
                    Label:
                        text: 'CHANNEL SETTINGS'
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    Label:
                        text: 'DAQmx Device Name: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        hint_text: 'PXI1Slot2'
                        multiline: False
                    Label:
                        text: 'AI Channel Number: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        input_filter: int
                        hint_text: '0'
                        multiline: False
                    Label:
                        text: 'Max Voltage: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        input_filter: int
                        hint_text: '5'
                        multiline: False
                    Label:
                        text: 'Min Voltage: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        input_filter: int
                        hint_text: '-5'
                        multiline: False
                    Label:
                        text: 'Terminal Configuration: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        hint_text: 'DEFAULT'
                        multline: False
                BoxLayout
                    orientation:'vertical'
                    GridLayout:
                        rows: 4
                        cols: 2
                        Label:
                        Label:
                            text: 'TIMING SETTINGS'
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        Label:
                            text: 'Sample Clock Source: '
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        TextInput:
                        Label:
                            text: 'Sample Rate: '
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        TextInput:
                            input_filter: int
                        Label:
                            text: 'Number of Samples: '
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        TextInput:
                            input_filter: int
                    GridLayout:
                        rows: 1
                        cols: 2
                        Label:
                            text: 'Error: '
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        TextInput:
                            multiline: False
                               
'''


# Function to launch the run process
def launch_run_process(task_configuration, ui_queue, cmd_queue):
    """
    This method launches the run process using multiprocessing.Process(). This process will use the configuration
    data provided at __init__ to create, configure, start, read from, and stop the NI
    DAQmx task. The run_process can be terminated using the destroy_run_process method below.
    """

    new_reader = AnalogInputReader(task_configuration=task_configuration,
                                   ui_queue=ui_queue, cmd_queue=cmd_queue)
    new_reader.run_process()


# Function to safely close and kill the run process
def destroy_run_process(reader_process, ui_queue, cmd_queue):
    """
    This method properly shuts down the currently running run_process using a specific queue message
    """
    stop_msg = GLOBAL_STOP
    cmd_queue.put(stop_msg)
    # Empty the UI queue enabling us to properly shut down our process
    while not ui_queue.empty():
        ui_queue.get()
    # After the command queue sends the stop message 'S', we wait for the finished message 'F'. If we receive it,
    # we know the DAQmx task has safely cleared and closed itself, thus we can safely close the reader process.
    cmd_queue.get(block=True, timeout=None)
    reader_process.kill()


# Guard allowing use to separate the Kivy logic entirely from the multiprocessing DAQmx functions. We have to keep
# all Kivy imports here to prevent Windows from launching another window when we launch a new process. This is
# discussed in detail here: https://github.com/kivy/kivy/issues/4744
if __name__ == "__main__":
    from kivy.config import Config

    Config.set('input', 'mouse', 'mouse,disable_on_activity')

    from kivy.core.window import Window

    # Set the minimum window size as the default app launch size
    window_sizes = Window.size
    Window.minimum_width, Window.minimum_height = window_sizes

    from kivy.lang import Builder
    from kivy.app import App
    from kivy.clock import Clock
    from graph_generator import GraphGenerator


    class MyApp(App):
        """
        Main kivy app class
        """

        def build(self):
            """ Kivy method for building the app by returning a widget """
            self.i = 0
            # TODO: Replace these hard-coded default values with the kivy utilities for creating and reading from an INI
            #  file at init
            self.task_configuration = {'sample_clock_source': 'OnBoardClock', 'sample_rate': 60,
                                       'samples_per_read': 30,
                                       'channel': 0, 'dev_name': 'PXI1Slot2', 'max_voltage': 5, 'min_voltage': -5,
                                       'terminal_configuration': TerminalConfiguration.DEFAULT}

            self.screen = Builder.load_string(KV)
            return self.screen

        def on_start(self, *args):
            """ Called right after build() """
            self.reset_graph()

        def set_touch_mode(self, mode):
            self.screen.figure_wgt.touch_mode = mode

        def home(self):
            self.screen.figure_wgt.home()

        def update_graph(self, _):
            try:
                self.y = float(self.ui_queue.get())
            except Exception:
                pass

            xdata = np.append(self.screen.figure_wgt.line1.get_xdata(), self.i)
            self.screen.figure_wgt.line1.set_data(xdata, np.append(self.screen.figure_wgt.line1.get_ydata(), self.y))
            if self.i > 2:
                self.screen.figure_wgt.xmax = np.max(xdata)
                if self.screen.figure_wgt.axes.get_xlim()[0] == self.screen.figure_wgt.xmin:
                    self.home()
                else:
                    self.screen.figure_wgt.figure.canvas.draw_idle()
                    self.screen.figure_wgt.figure.canvas.flush_events()

            self.i += 1

        def reset_graph(self):
            mygraph = GraphGenerator()
            self.screen.figure_wgt.figure = mygraph.fig
            self.screen.figure_wgt.axes = mygraph.ax1
            self.screen.figure_wgt.xmin = 0
            self.screen.figure_wgt.xmax = 50
            self.screen.figure_wgt.ymin = -5
            self.screen.figure_wgt.ymax = 5
            self.screen.figure_wgt.line1 = mygraph.line1
            self.home()

        def start_acquisition(self):
            """ Initialize the needed objects for the daqmx_reader AnalogInputReader() """
            self.ui_queue = Queue()
            self.cmd_queue = Queue()
            # Launches an instance of AnalogInputReader in another process using Process from Multiprocess. This in turn creates, configures, starts, and reads from a single-channel DAQmx analog input task.
            try:
                self.reader_process = Process(target=launch_run_process,
                                              args=(self.task_configuration, self.ui_queue, self.cmd_queue))
                self.reader_process.start()
                self.task_running = True
                # We can use the built-in features of the kivy state machine to schedule a reoccurring call at out desired rate. In this case, this rate corresponds to the maximum update time of the graph
                Clock.schedule_interval(self.update_graph, 1 / 60)
            except Exception as e:
                print(e)

        def stop_acquisition(self):
            """ Properly shuts down the task currently running, in turn destroying the currently running MultiProcessing
            process """
            try:
                destroy_run_process(reader_process=self.reader_process, ui_queue=self.ui_queue,
                                    cmd_queue=self.cmd_queue)
                Clock.unschedule(self.update_graph)
                self.i = 0
                self.y = 0
                self.task_running = False
            except Exception as e:
                print(e)

            self.reset_graph()

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


    myApp = MyApp()
    MyApp().run()
