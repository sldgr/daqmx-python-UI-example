"""
This code is originally authored by: pbellino
Source: https://github.com/pbellino/daq_nidaqmx_example
"""

import os
import numpy as np


class DataWriter:
    """
    Write data to file
    """

    def __init__(self, filename="Output_Data.csv"):
        super().__init__()

        if os.path.exists(filename):
            f = open(filename, 'w')
            f.close()
        self._file = open(filename, 'a')

        self._file.write("# Voltage (V)\n")

    def write_data(self, incoming_data):
        write_data = incoming_data.T
        np.savetxt(self._file, write_data, fmt='%s', delimiter=',')

    def close_file(self):
        self._file.close()


