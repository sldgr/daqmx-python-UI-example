<h3 align="center">DAQmx with Kivy</h3>

  <p align="center">
    Analog Input - Continuous Voltage
  </p>
  <p align="center">
    Display and Logging
  </p>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
      <ul>
        <li><a href="#acknowledgments">Acknowledgments</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

This is a Python take on the LabVIEW built-in example VI called Voltage - Continuous Input. Like the G-code equivalent,
this code features the ability to configure, start and stop a DAQmx single-channel analog input voltage task. With real
or simulated NI (National Instruments) hardware Other features worth mentioning include:

1. Use of Kivy, a cross-platform NUI development framework for python allowing easy separation of a UI layout and
   business logic
2. Real-time, (60+ FPS) graph display with home, zoom, and pan
3. Automatic logging of acquired data to a .csv file
4. Use of the python multiprocessing package to separate the Kivy App process from the DAQmx Stream Reader process

### Built With

* [Kivy](https://kivy.org/#home/)
* [NI DAQmx](https://nidaqmx-python.readthedocs.io/en/latest/)
* [Numpy](https://numpy.org/doc/stable/index.html)
* [Matplotlib](https://matplotlib.org/)

### ACKNOWLEDGEMENTS

* [mp_007's kivy_matplotlib_widget](https://github.com/mp-007/kivy_matplotlib_widget) - Used in the UI with code taken
  from real-time plotting examples
* [pbellino's daq_nidaqmx_example](https://github.com/pbellino/daq_nidaqmx_example) - Inspiration and borrowed fie
  writer

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

Get a local copy up and running follow these steps.

### Prerequisites

What you need before proceeding with the installation:

* Windows 10

* Python 3.9 (3.10 or later not supported)
  ```sh
  https://www.python.org/downloads/
  ```

* Pip
  ```sh
  py -m pip install --upgrade pip
  py -m pip --version
  ```

* Virtualenv
  ```sh
  py -m pip install --user virtualenv
  ```

* NI DAQmx Full Driver (Latest Version) <- Needed for NI MAX
  ```sh
  https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html#428058
  ```

### Installation

1. Clone the repo (or simply download as zip and then unzip):
   ```sh
   git clone https://github.com/sldgr/daqmx-python-UI-example
   ```
2. Update pip and other installation dependencies:
      ```sh
   py -m pip install --upgrade pip setuptools virtualenv
   ```
3. Navigate to your repo:
   ```sh
   cd <repo>
   ```
4. Create a virtual environment:
   ```sh
   py -m venv env
   ```

5. Activate the virtual environment:
   ```sh
   .\env\Scripts\activate
   ```

6. Install necessary packages from requirements.txt:
   ```sh
   py -m pip install -r requirements.txt
   ```
7. (Optional for simulated hardware):

    1. Open NI MAX (Measurement & Automation Explorer)
    2. Right-click > 'My System > Devices and Interfaces' and select 'Create New...'
    3. Select 'Simulated NI-DAQmx Device or Modular Instrument'
    4. Select 'Finish'
    5. Select any device that supports analog input. (e.g. PXIe-6368)
    6. Select a desired PXI chassis and slot # (or use defaults)
    7. Verify the simulated device is working by right-clicking and selecting ' Test Panel...' and then hitting 'Start'
       when it opens. Verify you see a signal.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->

## Usage

To run, simply use the following command in the top-level of the repository with the virtual environment env running:

   ```sh
   .\python daqmx_with_kivy.py
   ```

<p align="right">(<a href="#top">back to top</a>)</p>




<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any
contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also
simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- CONTACT -->

## Contact

[Cole Harding](https://www.linkedin.com/in/coleharding/) - cole.d.harding@gmail.com

Project Link: [https://github.com/sldgr/daqmx-python-UI-example](https://github.com/sldgr/daqmx-python-UI-example)

<p align="right">(<a href="#top">back to top</a>)</p>



