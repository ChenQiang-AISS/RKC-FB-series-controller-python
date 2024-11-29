import logging
import unittest
from unittest.mock import patch, MagicMock
from fb_controller.rkc_communication import RKCCommunication
from fb_controller.constants import ACK, EOT, NAK, ENQ
from fb_controller.utils import calculate_bcc

logging.basicConfig(level=logging.DEBUG)

class TestRKCCommunication(unittest.TestCase):
    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_set_value_with_ack(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Set up mock_serial_obj.read to return ACK.encode('ascii')
        mock_serial_obj.read.return_value = ACK.encode('ascii')

        # Call the set_value method
        comm.set_value(-150)

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 3)
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))
        mock_serial_obj.write.assert_any_call(b'01\x02S1-0150.0\x03V')
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_set_value_with_nak(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj
        # Set up mock_serial_obj.read to return NAK.encode('ascii') at first call
        # then ACK.encode('ascii') at second call
        mock_serial_obj.read.side_effect = [NAK.encode('ascii'), ACK.encode('ascii')]

        # Call the set_value method
        comm.set_value(-150)

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 5)
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))
        mock_serial_obj.write.assert_any_call(b'01\x02S1-0150.0\x03V')
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))
        mock_serial_obj.write.assert_any_call(b'01\x02S1-0150.0\x03V')
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))

        with self.assertRaises(ValueError):
            comm.set_value('a')

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_set_value_with_abnormal_response(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj
        # Set up mock_serial_obj.read to return NAK.encode('ascii') at first call
        # then ACK.encode('ascii') at second call
        mock_serial_obj.read.side_effect = ['aaa']

        # Call the set_value method
        self.assertIsNone(comm.set_value(-150))
        

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_read_value_successfully(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Set up mock_serial_obj.read to return -150.0
        mock_serial_obj.read_until.side_effect = [b'\x02M1-0150.0\x03']
        mock_serial_obj.read.side_effect = [b'H']

        # Call the set_value method
        result = comm.read_value()
        unittest.TestCase().assertEqual(result, -150.0)

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 2)
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))
        mock_serial_obj.write.assert_any_call(b'01M1\x05')

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_read_value_failed_once(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Set up mock_serial_obj.read to return -150.0
        mock_serial_obj.read_until.side_effect = [b'\x02M1-0150.0\x03']*2
        mock_serial_obj.read.side_effect = [b'K', b'H']

        # Call the set_value method
        result = comm.read_value()
        unittest.TestCase().assertEqual(result, -150.0)

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 3)
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))
        mock_serial_obj.write.assert_any_call(b'01M1\x05')
        mock_serial_obj.write.assert_any_call(NAK.encode('ascii'))

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_read_value_failed(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Set up mock_serial_obj.read to return -150.0
        mock_serial_obj.read_until.side_effect = [b'\x02M1-0150.0\x03']*3 + [b'']
        mock_serial_obj.read.side_effect = [b'K', b'L', b'M', b'']

        # Call the set_value method
        result = comm.read_value()
        unittest.TestCase().assertIsNone(result)

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 5)
        mock_serial_obj.write.assert_any_call(EOT.encode('ascii'))
        mock_serial_obj.write.assert_any_call(b'01M1\x05')
        mock_serial_obj.write.assert_any_call(NAK.encode('ascii'))

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_select_with_abnormal_response(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Set up mock_serial_obj.read to return ACK.encode('ascii')
        mock_serial_obj.read.return_value = b'aaa'

        # Call the set_value method
        result = comm.select('M1', '1')

        # Assert that the _send_eot method was called
        self.assertFalse(result)

class TestPrivateMethods(unittest.TestCase):
    @patch('fb_controller.rkc_communication.serial.Serial')
    def test__send_enq(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Call the _send_enq method
        comm._send_enq()

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 1)
        mock_serial_obj.write.assert_any_call(ENQ.encode('ascii'))

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test__send_ack(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Call the _send_enq method
        comm._send_ack()

        # Assert that the _send_eot method was called
        self.assertEqual(mock_serial_obj.write.call_count, 1)
        mock_serial_obj.write.assert_any_call(ACK.encode('ascii'))
    
    def test__validate_response(self):
        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")

        result = comm._validate_response(b'\x02M1-0120.9\x03F')
        self.assertTrue(result)

        result = comm._validate_response(b'\x02M1-0120.0\x03Q')
        self.assertFalse(result)

        result = comm._validate_response(b'M1-0120.0')
        self.assertFalse(result)
        
    def test__parse_response(self):
        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")

        result = comm._parse_response(b'\x02M1-0150.0\x03')
        self.assertEqual(result, '-0150.0')
        
        result = comm._parse_response(b'M1-0150.0')
        self.assertIsNone(result)

class TestUtils(unittest.TestCase):
    def test_calculate_bcc(self):
        result = calculate_bcc(b'M1-0120.9\x03')
        self.assertEqual(result, b'F')
        with self.assertRaises(ValueError):
            result = calculate_bcc(1)
            
class TestContext(unittest.TestCase):
    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_enter_and_exit(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Test that the __enter__ method was called correctly
        with comm:
            self.assertIsNotNone(comm)

        # Test that the __exit__ method was called correctly
        mock_serial_obj.close.assert_called_once()

    @patch('fb_controller.rkc_communication.serial.Serial')
    def test_close(self, mock_serial):
        # Create a mock serial object
        mock_serial_obj = MagicMock()
        mock_serial.return_value = mock_serial_obj

        # Create an instance of RKCCommunication with the mock serial object
        comm = RKCCommunication(port="COM3", baudrate=19200, address="01")
        comm.ser = mock_serial_obj

        # Call the close() method
        comm.close()

        # Verify that the close() method was called on the ser object
        mock_serial_obj.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()