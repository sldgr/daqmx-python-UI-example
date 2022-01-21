"""
Portions of this code are originally authored by: pbellino
Source: https://github.com/pbellino/daq_nidaqmx_example
"""

from multiprocessing import Process, Queue
from time import sleep

import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogSingleChannelReader

from file_writer import DataWriter

""" GLOBAL CONSTANTS """
GLOBAL_STOP = 'S'


def launch_run_process(task_configuration, ui_queue, cmd_queue):
    """
    This method launches the run process using multiprocessing.Process(). This process will use the configuration
    data provided at __init__ to create, configure, start, read from, and stop the NI
    DAQmx task. The run_process can be terminated using the destroy_run_process method below.
    """

    new_reader = AnalogInputReader(task_configuration=task_configuration,
                                   ui_queue=ui_queue, cmd_queue=cmd_queue)
    reader_process = Process(target=new_reader.run_process)
    reader_process.daemon = False
    reader_process.start()

    return reader_process


def destroy_run_process(reader_process, ui_queue, cmd_queue):
    global GLOBAL_STOP
    """
    This method properly shuts down the currently running run_process using a specific queue message
    """
    stop_msg = GLOBAL_STOP
    cmd_queue.put(stop_msg)

    """Empty both queues now so the caller of these methods can reuse the same queues if we want to launch a new 
    process. You have to manually do this as far as I am aware but there may be a better option here. """
    while not ui_queue.empty():
        ui_queue.get()
    reader_process.join()


class AnalogInputReader:
    """
    Class for creating, configuring, running, and closing a DAQmx task. This class should be called in a separate
    thread or process to allow for continuous acquisition in the read method with timing controlled by the DAQmx read
    method
    """

    def __init__(self, task_configuration, ui_queue, cmd_queue):
        """
        task_configuration = {sample_clock_source, sample_rate, samples_per_read, channel, dev_name, max_voltage,
        min_voltage, terminal_configuration}
        """
        self.sample_clock_source = task_configuration['sample_clock_source']
        self.sample_rate = task_configuration['sample_rate']
        self.samples_per_read = task_configuration['samples_per_read']
        self.channel = task_configuration['channel']
        self.dev_name = task_configuration['dev_name']
        self.min_voltage = task_configuration['min_voltage']
        self.max_voltage = task_configuration['max_voltage']
        self.terminal_configuration = task_configuration['terminal_configuration']
        self.ui_queue = ui_queue
        self.cmd_queue = cmd_queue
        # Create an empty numpy array to use for DAQmx stream reading
        self.input_data = np.empty(shape=(self.samples_per_read,))

    def run_process(self):
        global GLOBAL_STOP
        """
        Read from the DAQmx task which is acquiring at sample_rate. This method should be run in its own thread or
        process to allow for the DAQmx Read methods timeout to control the loop rate. Each loop iteration acquires
        samples_per_read and adds the samples to both the io and ui queues for logging and display. The default
        timeout is 10 seconds.
        """

        """ Initialize the data writer for logging """
        self.writer = DataWriter()

        self.create_task()
        self.start_task()

        while True:
            try:
                """ Read from the DAQmx buffer the required number of samples on the configured channel """
                self.reader.read_many_sample(data=self.input_data, number_of_samples_per_channel=self.samples_per_read,
                                             timeout=10.0)
                """ Use the map keyword to more quickly append our data to the UI queue """
                list(map(self.ui_queue.put, self.input_data))
                """ Write our data to the data writer """
                self.writer.write_data(self.input_data)
            except Exception as e:
                break
            try:
                msg = self.cmd_queue.get(block=False)
            except Exception as e:
                msg = ""
            if msg == GLOBAL_STOP:
                break

        self.stop_task()
        self.writer.close_file()

    def create_task(self):
        """
        Create a DAQmx task with the provided configuration parameters
        """

        """ Create the task """
        self.task = nidaqmx.Task("Analog Input Task")
        """ Create a temp dict to pass multiple arguments more easily """
        chan_args = {
            "min_val": self.min_voltage,
            "max_val": self.max_voltage,
            "terminal_config": self.terminal_configuration
        }
        """ Build the proper channel name using the device + channel """
        channel_name = self.dev_name + "/ai" + str(self.channel)
        """ Add the DAQmx channel to the task """
        self.task.ai_channels.add_ai_voltage_chan(channel_name, **chan_args)
        """ Configure the timing of the task """
        self.task.timing.cfg_samp_clk_timing(rate=self.sample_rate, sample_mode=AcquisitionType.CONTINUOUS)

    def start_task(self):
        """
        Start the task and create the analog input channel reader
        """

        self.task.start()
        self.reader = AnalogSingleChannelReader(self.task.in_stream)

    def stop_task(self):
        """
        Stop and clear the DAQmx task
        """

        self.task.stop()
        self.task.close()


if __name__ == "__main__":
    """ 
    used for debug
    """
    smpl_clk = "OnboardClock"
    smpl_rt = 100
    smpl_per_ch = 10
    ch = 0
    dev_name = "PXI1Slot2"
    max_volt = 5
    min_vol = -5
    term_cfg = nidaqmx.constants.TerminalConfiguration.DEFAULT
    uiq = Queue()
    cmq = Queue()
    test_config = {'sample_clock_source': smpl_clk, 'sample_rate': smpl_rt, 'samples_per_read': smpl_per_ch,
                   'channel': ch, 'dev_name': dev_name, 'max_voltage': max_volt, 'min_voltage': min_vol,
                   'terminal_configuration': term_cfg}

    test = launch_run_process(task_configuration=test_config, ui_queue=uiq, cmd_queue=cmq)
    sleep(10)
    destroy_run_process(reader_process=test, ui_queue=uiq, cmd_queue=cmq)
