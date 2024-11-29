import logging
import serial
from .constants import EOT, ENQ, STX, ETX, ACK, NAK, DEFAULT_BAUDRATE, DEFAULT_TIMEOUT
from .utils import calculate_bcc


class RKCCommunication:
    """
    This class is the interface to communicate with the RKC controller using the
    serial communication protocol.

    Attributes:
        port (str): The serial port to use (e.g., 'COM3').
        address (str): The address of the controller (e.g., '00').
        baudrate (int): The baudrate of the serial communication (e.g., 19200).
        timeout (int): The timeout for the serial communication (e.g., 3).
        bytesize (serial.EIGHTBITS): The number of bits for the serial communication (e.g., 8).
        parity (serial.PARITY_NONE): The parity of the serial communication (e.g., None).
        stopbits (serial.STOPBITS_ONE): The number of stopbits for the serial communication 
                                        Choose 1 for 1 stopbit or 2 for 2 stopbits.
    """

    def __init__(self, port: str, address: str = "00", baudrate: int = DEFAULT_BAUDRATE,
                 timeout: int | float = DEFAULT_TIMEOUT, bytesize: int = serial.EIGHTBITS,
                 parity: int = serial.PARITY_NONE, stopbits: int = serial.STOPBITS_ONE,
                 max_retries: int = 3):
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.timeout = timeout
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.max_retries = max_retries
        self.ser: serial.Serial = None

    def __enter__(self) -> "RKCCommunication":
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the serial connection when exiting the context."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _send_eot(self):
        """Send EOT to initiate or terminate the data link."""
        self.ser.write(EOT.encode('ascii'))
        logging.debug("Sent EOT")

    def _send_enq(self):
        """Send ENQ to request data from the controller."""
        self.ser.write(ENQ.encode('ascii'))
        logging.debug("Sent ENQ")

    def _send_ack(self):
        """Send ACK to acknowledge correct data."""
        self.ser.write(ACK.encode('ascii'))
        logging.debug("Sent ACK")

    def _send_nak(self):
        """Send NAK to request retransmission of data."""
        self.ser.write(NAK.encode('ascii'))
        logging.debug("Sent NAK")

    def poll(self, identifier: str, memory_area: str = "", return_with_identifier: bool = False):
        """Polling procedure to request data from the controller.

        Args:
            identifier (str): The identifier of the data to be requested.
            memory_area (str): The memory area of the data to be requested.
            return_with_identifier (bool): Whether to return the identifier with the data.

        Returns:
            str: The data received from the controller.
        """
        self._send_eot()  # Data link initialization
        query = f"{self.address}{memory_area}{identifier}{ENQ}"
        self.ser.write(query.encode('ascii'))  # Send polling sequence
        logging.debug("Sent polling sequence: %s", query)

        retries = 0
        while retries <= self.max_retries:
            # BCC follows ETX
            response = self.ser.read_until(
                ETX.encode('ascii')) + self.ser.read(1)
            logging.debug("Received response: %s", response)

            if response and self._validate_response(response):
                return self._parse_response(response, return_with_identifier)
            elif response:
                # Send NAK if response is invalid
                self._send_nak()
                retries += 1
            else:
                logging.error("No response received or timeout occurred.")
                retries += 1

        logging.error("Maximum retries exceeded. Giving up.")
        return None

    def select(self, identifier: str, data: str):
        """Selecting procedure to send data to the controller.

        Args:
            identifier (str): The identifier of the data to be sent.
            data (str): The data to be sent.
            
        Returns:
            bool: True if the selection is successful, False otherwise.
        """
        self._send_eot()  # Data link initialization
        message = f"{self.address}{STX}{identifier}{data}{ETX}"
        bcc = calculate_bcc(f'{identifier}{data}{ETX}')
        message_with_bcc = f"{message}{bcc.decode('ascii')}".encode('ascii')
        self.ser.write(message_with_bcc)  # Send selecting sequence
        logging.debug("Sent selecting sequence: %s", message_with_bcc)

        ack = self.ser.read(1)  # Expect ACK from the controller
        if ack == ACK.encode('ascii'):
            self._send_eot()  # Terminate data link
            return True
        if ack == NAK.encode('ascii'):
            logging.debug("Received NAK, retransmitting: %s", message_with_bcc)
            return self.select(identifier, data)  # Retransmit
        else:
            logging.error("Unexpected response: %s", ack)
            return False

    def _validate_response(self, response: bytes) -> bool:
        """Validate the response using BCC."""
        stx_index = response.find(STX.encode('ascii'))
        etx_index = response.find(ETX.encode('ascii'))
        if stx_index != -1 and etx_index != -1:
            # Extract the data between STX and ETX, and include ETX for BCC calculation
            data = response[stx_index + 1:etx_index + 1]  # Include ETX in data
            # Extract BCC (1 byte immediately after ETX)
            bcc = response[etx_index + 1:etx_index + 2]  # BCC is 1 byte

            # Calculate BCC including ETX (Note: ETX included in data for BCC)
            calculated_bcc = calculate_bcc(data.decode('ascii'))
            logging.debug("Calculated BCC: %s, Received BCC: %s",
                          calculated_bcc, bcc)

            # Validate if calculated BCC matches the received BCC
            return bcc == calculated_bcc

        logging.debug("Invalid response: %s", response)
        return False

    def _parse_response(self, response: bytes, return_with_identifier=False) -> str | None:
        """Parse the response from the controller.
        
        Args:
            response (bytes): The response from the controller.
            return_with_identifier (bool): Whether to return the identifier with the data.
        
        Returns:
            str|None: The data received from the controller, or None if parsing fails.
        """
        stx_index = response.find(STX.encode('ascii'))
        etx_index = response.find(ETX.encode('ascii'))

        if stx_index != -1 and etx_index != -1:
            # Extract the data between STX and ETX
            data = response[stx_index + 1:etx_index].decode('ascii')
            identifier = data[:2]
            value = data[2:]

            if return_with_identifier:
                return identifier, value
            return value

        logging.error("Failed to parse response: %s", response)
        return None

    def read_value(self):
        """Wrapper for reading the process value (PV) using M1 command."""
        result = self.poll(identifier="M1", return_with_identifier=True)
        if result:
            identifier, value = result
            logging.info("Read Value (M1): Identifier: %s, Value: %s", 
                         identifier, value)
            # Assuming the value is a float, adjust as needed
            return float(value)
        logging.error("Failed to read value (M1).")
        return None

    def set_value(self, value: int | float):
        """Wrapper for setting a value using S1 command."""
        if isinstance(value, (int, float)):
            # Format to match controller's expected format (e.g., '00100.0')
            formatted_value = f"{value:07.1f}"
            success = self.select(identifier="S1", data=formatted_value)
            if success:
                logging.info("Successfully set value (S1): %s",
                             formatted_value)
            else:
                logging.error("Failed to set value (S1).")
        else:
            raise ValueError("The value must be a number (int or float).")

    def close(self):
        """Close the serial connection."""
        self.ser.close()
