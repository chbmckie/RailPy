# RailPy

A python program designed to provide details on the next train departing any Network Rail or RTT Enabled Railway Station in the UK.

# Installation

To install and use the program succesfully, follow the below steps:

## **Connecting to the RealTimeTrains API**

To successfully connect to the API, follow the following steps:

1. Paste in your API Username and Passkey into the `~/assets/EXAMPLE_apiKeys.py` and save.
    1. *(Ensure the API Password is the one found in the API Portal, and not the one used to login to your API Account.)*
2. Rename the file to `apiKeys.py`.

## **Installing the DotMatrix Font**

### MacOS

1. Double-click on the file `~/assets/dotMatrix.ttf`  to open it in Font Book.
2. In Font Book, click the *"Install Font"* button. This will install the font on your system.

### Windows

1. Right-click on the file `~/assets/dotMatrix.ttf` to show the context menu.
2. In the context menu, select the *"Install"* option to open Font Viewer and automatically install the font.

### Linux

1. Navigate to the `~/assets/` directory using the `cd` command.
    1. `cd path/to/RailPy/assets/`
2. Copy the file into the fonts directory *(usually* `/usr/share/fonts/truetype/`*)* using the `cp` command.
    1.  `sudo cp dotMatrix.ttf /usr/share/fonts/truetype/`
3. Refresh the font cache using the `fc-cache` command.
    1. `sudo fc-cache -f -v`