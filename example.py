import logging
from fb_controller.rkc_communication import RKCCommunication

logging.basicConfig(level=logging.DEBUG)

# Automatically manage the opening and closing of the communication
with RKCCommunication(port="COM3", baudrate=19200, address="01") as comm:
    # Read process value (PV) using M1 command
    current_value = comm.read_value()
    if current_value is not None:
        print(f"Current Process Value (PV): {current_value}")
    
    sv_value = comm.poll(identifier="S1")
    print(f'Current Set Value (S1): {sv_value}')
    comm.set_value(-15.0)
    sv_value = comm.poll(identifier="S1")
    print(f'Current Set Value (S1): {sv_value}')
        
        