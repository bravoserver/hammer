from twisted.trial import unittest


class TestProtocol22(unittest.TestCase):
    """
    Can we handle a proper protocol 22 handshake

    C->S - Handshake Packet 0x02
    S->C - Handshake Packet 0x02 (- for offline, + for online)
    C->S - Login Packe      0x01
    """

    def test_proper_handshake(self):
        """
        TestCase: Proper handshake as shown in the class doc
        Result  : End with protocol claiming to be 22
        """

        # Initialize protocol to 0, this should be 22 by the end of the test
        protocol = 0
        self.assertEqual(protocol, 22)

    def test_handshake_only(self):
        """
        TestCase: Receive valid handshake packet - then no othes
        Result  : Timeout Error
        """

        # Placeholder for unwritten test
        self.assertEqual(1, 2)

    def test_non_handshake_packet(self):
        """
        TestCase: Start with a non-handshake (0x02) packet
        Result  : Timeout Error
        """

        # Placeholder for unwritten test
        self.assertEqual(1,2)
