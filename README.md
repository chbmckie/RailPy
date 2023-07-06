![RailPyBanner](https://github.com/chbmckie/RailPy/assets/132846485/22abe6e2-bb6f-44c3-97f8-ef8d154e2f8c)

# RailPy

RailPy is a python program designed to provide details on the next train departing any Network Rail or RTT Enabled Railway Station in the UK.

# Installation

To install and use the program successfully, follow the below steps:

## **Connecting to the RealTimeTrains API**

To successfully connect to the API, follow the following steps:

1. Run the code for the first time and the application should prompt you to input your API Details.
    1. *(Ensure the API Password is the one found in the API Portal, and not the one used to login to your API Account.)*
2. These details will then be saved to the file to `~/assets/apiKeys.json`.
    1. If these details are erroneous, this file will need to be deleted, and the application will again prompt you to enter these.

## **Installing the DotMatrix Font**

### MacOS

1. Double-click on the file `~/RailPy/assets/dotMatrix.ttf`  to open it in Font Book.
2. In Font Book, click the *"Install Font"* button. This will install the font on your system.

### Windows

1. Right-click on the file `~/RailPy/assets/dotMatrix.ttf` to show the context menu.
2. In the context menu, select the *"Install"* option to open Font Viewer and automatically install the font.

### Linux

1. Navigate to the `~/RailPy/assets/` directory using the `cd` command.
    1. `cd path/to/RailPy/assets/`
2. Copy the file into the fonts directory *(usually* `/usr/share/fonts/truetype/`*)* using the `cp` command.
    1.  `sudo cp dotMatrix.ttf /usr/share/fonts/truetype/`
3. Refresh the font cache using the `fc-cache` command.
    1. `sudo fc-cache -f -v`
