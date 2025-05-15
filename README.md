# RKC-FB-series-controller-python, a Python Library for FB100/400/900 Controllers

This Python library facilitates communication with the FB100/400/900 controllers using the RKC protocol over serial communication. It implements polling/selecting methods as defined in the ANSI X3.28-1976 standard, allowing for reading and writing data between a host computer and the controller.

## Features
- Polling data from the controller (e.g., Measured Value (M1))
- Setting values on the controller (e.g., Setpoint Value (S1))
- Block Check Character (BCC) validation for data integrity
- Handles communication control characters like STX, ETX, ACK, NAK, and EOT

For the details of RKC protocol related to FB series controller, refer to [RKC_protocol](RKC_protocol.md).


## Usage Example
``` python
from fb_controller.rkc_communication import RKCCommunication

# Automatically manage the opening and closing of the communication
with RKCCommunication(port="COM3", baudrate=19200, address="01") as comm:
    # Read process value (PV) using M1 command
    current_value = comm.read_value()
    if current_value is not None:
        print(f"Current Process Value (PV): {current_value}")

    # Set a new value for Set Value (SV) using S1 command
    new_value = 120.0  # Set new value as 120.0
    comm.set_value(new_value)
```

## Installation

```
pip install -e .
```
