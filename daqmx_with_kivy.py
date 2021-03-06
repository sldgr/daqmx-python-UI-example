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
import queue
from multiprocessing import Queue
from time import sleep

import numpy as np
from nidaqmx.constants import TerminalConfiguration

from daqmx_reader import AnalogInputReader, Process

# Global Constants
GLOBAL_STOP = 'S'
# Define the entire UI layout and event functionality with the KV language. This could also be its own .kv file.
KV = '''
#:import MatplotFigure graph_widget
Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        padding: [20, 20, 20, 20]
        BoxLayout
            size_hint_y: .1
            Label: 
                text: 'DAQmx - Continuous Analog Input'
                text_size: self.size
                font_size: 20
                halign: 'left'
                valign: 'middle'
            Label: 
                text: 'Press Enter to save any change'
                text_size: self.size
                halign: 'right'
                valign: 'middle'
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
                        on_text_validate: app.update_device_name(self.text)
                    Label:
                        text: 'AI Channel Number: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        hint_text: '0'
                        multiline: False
                        on_text_validate: app.update_channel_number(self.text)
                    Label:
                        text: 'Max Voltage (V): '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        hint_text: '5'
                        multiline: False
                        on_text_validate: app.update_max_voltage(self.text)
                    Label:
                        text: 'Min Voltage (V): '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        hint_text: '-5'
                        multiline: False
                        on_text_validate: app.update_min_voltage(self.text)
                    Label:
                        text: 'Terminal Configuration: '
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                    TextInput:
                        hint_text: 'DEFAULT'
                        multiline: False
                        on_text_validate: app.update_terminal_configuration(self.text)
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
                            hint_text: 'OnboardClock'
                            multiline: False
                            on_text_validate: app.update_sample_clock_source(self.text)
                        Label:
                            text: 'Sample Rate (Hz): '
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        TextInput:
                            hint_text: '1000'
                            multiline: False
                            on_text_validate: app.update_sample_rate(self.text)
                        Label:
                            text: 'Samples Per Channel: '
                            text_size: self.size
                            halign: 'right'
                            valign: 'middle'
                        TextInput:
                            hint_text: '100'
                            multiline: False
                            on_text_validate: app.update_number_of_samples(self.text)
                    BoxLayout:
                        size_hint_y: .5
                        GridLayout:
                            rows: 1
                            cols: 2
                            Label:
                                text: 'Error: '
                                text_size: self.size
                                halign: 'right'
                                valign: 'middle'
                            TextInput:
                                multiline: True
                                background_color: [.8, .8, .8, 1]
                                id: err                          
'''

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
            # Counter that counts loop iterations of the update_graph method which corresponds directly to sample #
            self.i = 0
            # Floating point variable we use for updating the graph
            self.y = float(0)
            # Default configuration parameters for the DAQmx task
            # TODO: Replace these hard-coded default values with the kivy utilities for creating and reading from an INI
            #  file at init
            self.task_configuration = {'sample_clock_source': 'OnBoardClock', 'sample_rate': 60,
                                       'samples_per_read': 30,
                                       'channel': 0, 'dev_name': 'PXI1Slot2', 'max_voltage': 5, 'min_voltage': -5,
                                       'terminal_configuration': TerminalConfiguration.DEFAULT}
            self.task_running = False
            self.screen = Builder.load_string(KV)
            return self.screen

        def on_start(self, *args):
            """ Called right after build() """
            self.reset_graph()

        def on_stop(self):
            """ Called at app exit """
            if self.task_running:
                self.stop_acquisition()

        def set_touch_mode(self, mode):
            """ Sets the touch mode """
            self.screen.figure_wgt.touch_mode = mode

        def home(self):
            """ Returns the graph widget to its home pan position """
            self.screen.figure_wgt.home()

        def update_graph(self, _):
            """ Updates the graph widget with the newest sample from the reader process """
            if self.reader_process.is_alive():
                # If the reader process is alive, we can keep reading data from our queue and checking for errors
                if self.reader_process.exception:
                    # If the process has an error, read it and then stop it
                    self.read_error()
                    self.stop_acquisition()
                else:
                    try:
                        # Try to get from our queue immediately. Only plot if we get data.
                        self.y = self.ui_queue.get_nowait()
                        # Update our x data with our current sample count
                        xdata = np.append(self.screen.figure_wgt.line1.get_xdata(), self.i)
                        # Update the y data
                        self.screen.figure_wgt.line1.set_data(xdata,
                                                              np.append(self.screen.figure_wgt.line1.get_ydata(),
                                                                        self.y))
                        if self.i > 2:
                            self.screen.figure_wgt.xmax = np.max(xdata)
                            if self.screen.figure_wgt.axes.get_xlim()[0] == self.screen.figure_wgt.xmin:
                                self.home()
                            else:
                                self.screen.figure_wgt.figure.canvas.draw_idle()
                                self.screen.figure_wgt.figure.canvas.flush_events()
                        self.i += 1
                    except queue.Empty:
                        # Do not update the graph when we don't have data.
                        pass
            else:
                # This catches the first call to update_graph
                self.read_error()
                self.stop_acquisition()

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
            self.ack_queue = Queue()
            # Create a new instance of the reader class with the provided configuration and queues
            self.new_reader = AnalogInputReader(task_configuration=self.task_configuration,
                                                ui_queue=self.ui_queue, cmd_queue=self.cmd_queue,
                                                ack_queue=self.ack_queue)
            # Create a new multiprocessing process using the Process class of daqmx_reader.py. This is simply a
            # wrapper around the regular multiprocessing Process but with the ability to return an error
            self.reader_process = Process(target=self.new_reader.run)
            # The DAQmx reader process will start at this call
            self.reader_process.start()
            # Give the task a second to configure itself
            sleep(1)
            # Schedule the rate at which we update our graph and
            Clock.schedule_interval(self.update_graph, 1 / 120)
            self.task_running = True

        def stop_acquisition(self):
            """ Properly shuts down the task currently running, in turn destroying the currently running MultiProcessing
            process """
            # Stop the graph from updating
            Clock.unschedule(self.update_graph)
            # Reset the counter and y value
            self.i = 0
            self.y = float(0)

            if self.reader_process.is_alive():
                # After the command queue sends the stop message 'S', we wait for the finished message 'F'. When we
                # receive it, we know the DAQmx task has safely cleared and closed itself, thus we can safely close the
                # reader process.
                self.cmd_queue.put(GLOBAL_STOP)
                self.ack_queue.get(block=True, timeout=None)
                self.reader_process.terminate()
                self.reader_process.join()
            else:
                # Since the reader terminated on error, it's our job to empty the queues for proper shutdown
                while not self.ui_queue.empty():
                    self.ui_queue.get()
                while not self.cmd_queue.empty():
                    self.cmd_queue.get()
                while not self.ack_queue.empty():
                    self.ack_queue.get()
                self.reader_process.join()

            self.task_running = False
            self.reset_graph()

        def read_error(self):
            self.error = self.reader_process.exception
            self.update_error_display(self.error)

        def update_device_name(self, new_value):
            """ Updates the real or simulated DAQmx device to be used for the DAQmx task """
            self.task_configuration['dev_name'] = new_value

        def update_channel_number(self, new_value):
            """ Updates the physical analog input channel to be used for the DAQmx task """
            try:
                self.task_configuration['channel'] = int(new_value)
            except Exception as e:
                e = 'Input must be an integer'
                self.update_error_display(e)

        def update_max_voltage(self, new_value):
            """ Updates the max voltage to be used for the DAQmx task """
            try:
                self.task_configuration['max_voltage'] = int(new_value)
            except Exception as e:
                e = 'Input must be an integer'
                self.update_error_display(e)

        def update_min_voltage(self, new_value):
            """ Updates the min voltage to be used for the DAQmx task """
            try:
                self.task_configuration['min_voltage'] = int(new_value)
            except Exception as e:
                e = 'Input must be an integer'
                self.update_error_display(e)

        def update_terminal_configuration(self, new_value):
            """ Updates the terminal configuration to be used for the DAQmx task """
            if new_value == 'DEFAULT':
                self.task_configuration['terminal_configuration'] = TerminalConfiguration.DEFAULT
            elif new_value == 'RSE':
                self.task_configuration['terminal_configuration'] = TerminalConfiguration.RSE
            elif new_value == 'NRSE':
                self.task_configuration['terminal_configuration'] = TerminalConfiguration.NRSE
            elif new_value == 'DIFFERENTIAL':
                self.task_configuration['terminal_configuration'] = TerminalConfiguration.DIFFERENTIAL
            elif new_value == 'PSEUDODIFFERENTIAL':
                self.task_configuration['terminal_configuration'] = TerminalConfiguration.PSEUDODIFFERENTIAL
            else:
                self.task_configuration['terminal_configuration'] = TerminalConfiguration.DEFAULT
                self.update_error_display('Invalid terminal configuration. Valid options include DEFAULT, RSE, NRSE, '
                                          'DIFFERENTIAL,PSEUDODIFFERENTIAL')

        def update_sample_clock_source(self, new_value):
            """ Updates the sample clock source to be used for the DAQmx task """
            self.task_configuration['sample_clock_source'] = new_value

        def update_sample_rate(self, new_value):
            """ Updates the sample rate to be used for the DAQmx task """
            try:
                self.task_configuration['sample_rate'] = int(new_value)
            except Exception as e:
                e = 'Input must be an integer'
                self.update_error_display(e)

        def update_number_of_samples(self, new_value):
            """ Updates the sample rate to be used for the DAQmx task """
            try:
                self.task_configuration['samples_per_read'] = int(new_value)
            except Exception as e:
                e = 'Input must be an integer'
                self.update_error_display(e)

        def update_error_display(self, error):
            """ Updates the error display with a new error string """
            self.screen.ids.err.text = str(error)

    myApp = MyApp()
    MyApp().run()
