"""
daqmx_reader.py: This class implements the DAQmx analog input stream reader using the callers provided configuration
parameters. In a sense it is a mini API allowing a caller to very easily launch a reader in another thread or process.

Inspiration and assistance provided by the following:
https://github.com/pbellino/daq_nidaqmx_example
https://nidaqmx-python.readthedocs.io
"""

import multiprocessing
import queue
import traceback

import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogSingleChannelReader

from file_writer import DataWriter

# Global Constants
# TODO: These should be defined elsewhere as they are reused in multiple files in this app
GLOBAL_STOP = 'S'
GLOBAL_ACK = 'F'


class AnalogInputReader:
    """
    Class for creating, configuring, running, and closing a DAQmx task. You must initialize, run and close the reader
    in a separate thread or process to allow the run_process to run independently of your main application.
    """

    def __init__(self, task_configuration, ui_queue, cmd_queue, ack_queue):
        """
        Creates a new AnalogInputReader with the specified task configuration and queue references.

        :param task_configuration:
                    self.task_configuration = {'sample_clock_source': 'OnBoardClock', 'sample_rate': 60,
                                       'samples_per_read': 30,
                                       'channel': 0, 'dev_name': 'PXI1Slot2', 'max_voltage': 5, 'min_voltage': -5,
                                       'terminal_configuration': TerminalConfiguration.DEFAULT}
        :param ui_queue: A multiprocessing queue that sends acquired float_64 data back to the caller
        :param cmd_queue: A multiprocessing queue that receives a stop command character from the caller
        :param ack_queue: A multiprocessing queue that send an ACK command back to the caller
        """
        self._exception = None
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
        self.ack_queue = ack_queue
        # Create an empty numpy array of proper size to use for DAQmx stream reading
        self.input_data = np.empty(shape=(self.samples_per_read,))

    def run(self):
        """
        Read from the DAQmx task which is acquiring at sample_rate.Each loop iteration acquires samples_per_read and
        adds the samples to both the io and ui queues for logging and display. The default timeout is 10 seconds.
        """
        # Initialize the data writer for logging
        self.writer = DataWriter()
        # Try to create the task using the provided task parameters at __init__
        self.create_task()
        # Run the task if it was created successfully
        self.start_task()
        while True:
            # Read from the DAQmx buffer the required number of samples on the configured channel, waiting,
            # if needed, up to timeout for the requested number_of_samples_per_channel becomes available
            self.reader.read_many_sample(data=self.input_data,
                                         number_of_samples_per_channel=self.samples_per_read,
                                         timeout=10.0)
            # Use the map keyword to more quickly append our data to the UI queue
            list(map(self.ui_queue.put, self.input_data))
            # Write our data to the data writer
            try:
                msg = self.cmd_queue.get(block=False)
            except queue.Empty:
                # The queue get method will throw this exception if empty. We don't care if it's empty,
                # so we ignore it
                msg = ""
            if msg == GLOBAL_STOP:
                # Exit when the caller sends a global stop
                break
        self.stop_task()
        self.writer.close_file()

    def create_task(self):
        """
        Create a DAQmx task with the provided configuration parameters
        """

        self.task = nidaqmx.Task("Analog Input Task")
        # Create a temp dict to pass multiple arguments more easily
        chan_args = {
            "min_val": self.min_voltage,
            "max_val": self.max_voltage,
            "terminal_config": self.terminal_configuration
        }
        # Build the proper channel name using the device + channel
        channel_name = self.dev_name + "/ai" + str(self.channel)
        # Add the DAQmx channel to the task
        self.task.ai_channels.add_ai_voltage_chan(channel_name, **chan_args)
        # Configure the timing of the task. Notice we do not specify the samples per channel. As this program only
        # supports continuous acquisitions, samples per channel simply specifies the DAQmx PC buffer size which
        # is usually ignored anyway as the default is sufficient.
        # For more info, see: https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YHpECAW&l=en-US
        self.task.timing.cfg_samp_clk_timing(rate=self.sample_rate, sample_mode=AcquisitionType.CONTINUOUS)

    def start_task(self):
        """
        Start the task and create the analog input channel reader
        """

        self.task.start()
        self.reader = AnalogSingleChannelReader(self.task.in_stream)

    def stop_task(self):
        """
        Stop and clear the DAQmx task, empty our queues
        """

        self.task.stop()
        self.task.close()
        # Flush our queues, so we can properly kill the process this is being run in
        while not self.ui_queue.empty():
            self.ui_queue.get()
        while not self.cmd_queue.empty():
            self.cmd_queue.get()
        while not self.ack_queue.empty():
            self.ack_queue.get()
        # Send the global ACK back to the caller letting it know we are ready to die
        self.ack_queue.put(GLOBAL_ACK)


class Process(multiprocessing.Process):
    """
    Class which returns child Exceptions to Parent.
    https://stackoverflow.com/a/33599967/4992248
    """

    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._parent_conn, self._child_conn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._child_conn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._child_conn.send((e, tb))
            # raise e  # You can still rise this exception if you need to

    @property
    def exception(self):
        if self._parent_conn.poll():
            self._exception = self._parent_conn.recv()
        return self._exception
