#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import unittest
import osc

_DGRAM_TWO_MESSAGES_IN_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    # First message.
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # Second message, same.
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

_DGRAM_EMPTY_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01")

_DGRAM_NESTED_MESS = (
    b"#bundle\x00"
    b"\x10\x00\x00\x00\x00\x00\x00\x00"
    # First message.
    b"\x00\x00\x00\x10"  # 16 bytes
    b"/1111\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # Second message, same.
    b"\x00\x00\x00\x10"  # 16 bytes
    b"/2222\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # Now another bundle within it, oh my...
    b"\x00\x00\x00$"  # 36 bytes.
    b"#bundle\x00"
    b"\x20\x00\x00\x00\x00\x00\x00\x00"
    # First message.
    b"\x00\x00\x00\x10"
    b"/3333\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # And another final bundle.
    b"\x00\x00\x00$"  # 36 bytes.
    b"#bundle\x00"
    b"\x15\x00\x00\x00\x00\x00\x00\x01"  # Immediately this one.
    # First message.
    b"\x00\x00\x00\x10"
    b"/4444\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")


class TestOSCPacket(unittest.TestCase):

    def test_two_messages_in_a_bundle(self):
        """Test parsing of two messages in bundle"""

        packet = osc.OSCPacket(_DGRAM_TWO_MESSAGES_IN_BUNDLE)
        self.assertEqual(2, packet.message.length)

    def test_empty_dgram(self):
        """Test empty datagram which must raise exception"""

        self.assertRaises(osc.OSCParseError, osc.OSCPacket, b'')

    def test_empty_bundle(self):
        """Test empty bundle datagram"""

        packet = osc.OSCPacket(_DGRAM_EMPTY_BUNDLE)
        self.assertEqual(0, packet.message.length)

    def test_nested_bundle(self):
        """Test nested bundle datagram"""

        packet = osc.OSCPacket(_DGRAM_NESTED_MESS)
        self.assertEqual(4, packet.message.length)


if __name__ == "__main__":
    unittest.main()
