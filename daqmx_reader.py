import queue

import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogSingleChannelReader

from file_writer import DataWriter

# GLOBAL_CONSTANTS
# TODO: These should be defined elsewhere as they are reused in multiple files
GLOBAL_STOP = 'S'


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
        """
        Read from the DAQmx task which is acquiring at sample_rate. This method should be run in its own thread or
        process to allow for the DAQmx Read methods timeout to control the loop rate. Each loop iteration acquires
        samples_per_read and adds the samples to both the io and ui queues for logging and display. The default
        timeout is 10 seconds.
        """

        # Initialize the data writer for logging
        self.writer = DataWriter()

        self.create_task()
        self.start_task()

        while True:
            try:
                # Read from the DAQmx buffer the required number of samples on the configured channel
                self.reader.read_many_sample(data=self.input_data, number_of_samples_per_channel=self.samples_per_read,
                                             timeout=10.0)
                # Use the map keyword to more quickly append our data to the UI queue
                list(map(self.ui_queue.put, self.input_data))
                # Write our data to the data writer
                self.writer.write_data(self.input_data)
            except Exception as e:
                print(e)
                break
            try:
                msg = self.cmd_queue.get(block=False)
            except queue.Empty:
                # We handle any queue get exception with no action. This is almost always
                msg = ""
            if msg == GLOBAL_STOP:
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
        Stop and clear the DAQmx task
        """

        self.task.stop()
        self.task.close()
        # This may seem strange, but the main app that launches this process while wait for any message from this
        # process
        self.cmd_queue.put('')
