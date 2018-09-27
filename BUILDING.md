# Running the code
This tool has been tested with python 3.5.3. The pyserial module is required, and this can be installed with pip:

    pip install pyserial

The script can then be run with the following command:

    python SerialTrafficGenerator.py

Alternatively the application can be compiled into a standalone executable with the following commands:

    pip install pyinstaller
    pyinstaller --onefile --windowed --icon=serialtrafficgenerator.ico --add-data serialtrafficgenerator.ico;. SerialTrafficGenerator.py
