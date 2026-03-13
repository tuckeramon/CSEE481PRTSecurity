# CSEE481PRTSecurity
---
## Getting Started

#### On the workstation computer
Note: The following instructions are specifically for the workstation computer in the lab room which is running Windows. Trying to run them on any other device will likely result in failure. Additionally, the following commands are for PowerShell, not command prompt (cmd).

In order to start the front- and back-end you must first install the required packages. To do this, you must first make sure that you are in the correct path by navigating to:

### `~/CSEE481PRTSecurity/SCIAI_broken/`

Once you are in the correct directory, run the following command:

### `pip install -r requirements.txt`

---
## On the HMI (Human-Machine Interface)

There is a touchscreen panel on the left side of the desktop computer's podium. In order to start the test bench, go to this touchscreen and verify that you are logged in to the admin account. This is shown in the information bar at the top of the screen. On the left side of the screen there is a button labeled "ALL STOP RESET". If this button is gray, press it and make sure it is yellow before you continue. Once this is complete, navigate to the PRT section by clicking the button in the bottom left.

Once on the correct page, ensure that "SYSTEM MAINTENENCE MODE" is not highlighted in yellow. On the right side of the screen, the button under "SYSTEM MODE SELECT" should read "PRT MODE". If this button says "SMART MANUFACTURING MODE", press it and it will change to say "PRT MODE". Once you have verifired this, tap the "START" button to start the test bench.

---
## Starting the Dashboard
After you have installed the required packages and checked the HMI, you can start the front-end and back-end simultaneously by using the command:

#### `py sys_run.py`

This will open a window prompting you to enter a username and password. Once you have entered your credentials, the front-end window will appear.

To verify that the back-end has successfully connected, view the output logs in the terminal. More than one reconnect attempt is normal.


---
## Navigating the Dashboard

### Selecting a cart

The first tab on the front-end is the PRT dashboard. On the left is a visual representation of the testbench with labeled circles representing each of the model PRT carts.

Clicking on any of the circles will select and highlight that cart. You may also use the drop-down selector on the right side of the dashboard to select a cart.

Note: This section of the dashboard is still a WIP, all carts are shown at all times as the system does not have a way to know what carts are currently being used. Carts will also likley be overlapping. It is suggested to to use the drop-down selection on the right of the dashboard.

### Sending a cart to a station

After selecting a cart, you may send it to one of the stations by using the drop down selector the right under "Select Station Destination". Once you have selected a station, click the "Send Cart to Station" button to send the instruction.

### Removing a cart from the test bench

Note: As of the writing of the documentation, the ability to remove a cart from a station has not yet been implemented. Therefore, this section should be updated and this text removed in accordance with future implementations.

After selecting a cart, you may remove it from the test bench by using the drop down selector on the right under "Select Unload Drop-off Area". Once you have selected an area, click the "Remove Active Cart" button to send the instruction.

#### Important Note:
The barcode scanners do not always read the barcode on the top of the carts, even if it looks like it was correctly read from the logging output. If the barcode is successfully read, the scanner should audibly beep once and flash a green light.