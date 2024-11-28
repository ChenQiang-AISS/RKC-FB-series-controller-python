import unittest
from fb_controller.rkc_communication import RKCCommunication

class TestRKCCommunication(unittest.TestCase):
    def setUp(self):
        self.comm = RKCCommunication(port="COM3", baudrate=19200, address="01")

    def test_polling(self):
        response = self.comm.poll(identifier="M1")
        self.assertIsNotNone(response)

    def tearDown(self):
        self.comm.close()

if __name__ == '__main__':
    unittest.main()
