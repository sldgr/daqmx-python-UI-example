"""
Portions of this code are originally authored by: pbellino
Source: https://github.com/pbellino/daq_nidaqmx_example
"""

import os
import numpy as np


class DataWriter:
    """
    Write data to file
    """

    def __init__(self, filename="Output_Data.txt"):
        super().__init__()

        if os.path.exists(filename):
            f = open(filename, 'w')
            f.close()
        self._file = open(filename, 'a')

        self._file.write("# I am the header\n")

    def write_data(self, incoming_data):
        np.savetxt(self._file, incoming_data.T)

    def close_file(self):
        self._file.close()
