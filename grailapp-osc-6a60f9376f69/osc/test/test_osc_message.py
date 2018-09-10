#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import unittest
import osc

# Datagrams sent by Reaktor 5.8 by Native Instruments (c).
_DGRAM_KNOB_ROTATES = (
    b"/FB\x00"
    b",f\x00\x00"
    b">xca=q")

_DGRAM_SWITCH_GOES_OFF = (
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"\x00\x00\x00\x00")

_DGRAM_SWITCH_GOES_ON = (
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

_DGRAM_NO_PARAMS = b"/SYNC\x00\x00\x00"

_DGRAM_ALL_STANDARD_TYPES_OF_PARAMS = (
    b"/SYNC\x00\x00\x00"
    b",ifsb\x00\x00\x00"
    b"\x00\x00\x00\x03"  # 3
    b"@\x00\x00\x00"  # 2.0
    b"ABC\x00"  # "ABC"
    b"\x00\x00\x00\x08stuff\x00\x00\x00")  # b"stuff\x00\x00\x00"

_DGRAM_ALL_NON_STANDARD_TYPES_OF_PARAMS = (
    b"/SYNC\x00\x00\x00"
    b",T"  # True
    b"F\x00")  # False

_DGRAM_UNKNOWN_PARAM_TYPE = (
    b"/SYNC\x00\x00\x00"
    b",fx\x00"  # x is an unknown param type.
    b"?\x00\x00\x00")


class TestOSCMessage(unittest.TestCase):

    def test_switch_goes_off(self):
        msg = osc.OSCMessage.parse(_DGRAM_SWITCH_GOES_OFF)

        self.assertEqual("/SYNC", msg.address)
        self.assertEqual(1, len(msg.args))
        self.assertTrue(type(msg.args[0]) == float)
        self.assertAlmostEqual(0.0, msg.args[0])

    def test_switch_goes_on(self):
        msg = osc.OSCMessage.parse(_DGRAM_SWITCH_GOES_ON)

        self.assertEqual("/SYNC", msg.address)
        self.assertEqual(1, len(msg.args))
        self.assertTrue(type(msg.args[0]) == float)
        self.assertAlmostEqual(0.5, msg.args[0])

    def test_knob_rotates(self):
        msg = osc.OSCMessage.parse(_DGRAM_KNOB_ROTATES)

        self.assertEqual("/FB", msg.address)
        self.assertEqual(1, len(msg.args))
        self.assertTrue(type(msg.args[0]) == float)

    def test_no_params(self):
        msg = osc.OSCMessage.parse(_DGRAM_NO_PARAMS)

        self.assertEqual("/SYNC", msg.address)
        self.assertEqual(0, len(msg.args))

    def test_all_standard_types_off_params(self):
        msg = osc.OSCMessage.parse(_DGRAM_ALL_STANDARD_TYPES_OF_PARAMS)

        self.assertEqual("/SYNC", msg.address)
        self.assertEqual(4, len(msg.args))
        self.assertEqual(3, msg.args[0])
        self.assertAlmostEqual(2.0, msg.args[1])
        self.assertEqual("ABC", msg.args[2])
        self.assertEqual(b"stuff\x00\x00\x00", msg.args[3])
        self.assertEqual(4, len(list(msg)))

    def test_all_non_standard_params(self):
        msg = osc.OSCMessage.parse(_DGRAM_ALL_NON_STANDARD_TYPES_OF_PARAMS)

        self.assertEqual("/SYNC", msg.address)
        self.assertEqual(2, len(msg.args))
        self.assertEqual(True, msg.args[0])
        self.assertEqual(False, msg.args[1])
        self.assertEqual(2, len(list(msg)))

    def test_raises_on_empty_datargram(self):
        self.assertRaises(osc.OSCParseError, osc.OSCMessage.parse, b'')

    def test_ignores_unknown_param(self):
        msg = osc.OSCMessage.parse(_DGRAM_UNKNOWN_PARAM_TYPE)

        self.assertEqual("/SYNC", msg.address)
        self.assertEqual(1, len(msg.args))
        self.assertTrue(type(msg.args[0]) == float)
        self.assertAlmostEqual(0.5, msg.args[0])

    def test_raises_on_incorrect_datagram(self):
        self.assertRaises(osc.OSCParseError, osc.OSCMessage.parse, b'foobar')

    def test_just_address(self):
        msg = osc.OSCMessage(address="/a/b/c")
        self.assertEqual("/a/b/c", msg.address)
        self.assertEqual(0, len(msg))

    def test_no_address_raises(self):
        self.assertRaises(ValueError, osc.OSCMessage, "")

    def test_wrong_param_raise(self):
        builder = osc.OSCMessage()
        self.assertRaises(ValueError, builder.add, "what?", 1)

    def test_all_param_types(self):
        builder = osc.OSCMessage(address="/SYNC")
        builder.add(4.0)
        builder.add(2)
        builder.add("value")
        builder.add(True)
        builder.add(False)
        builder.add(b"\x01\x02\x03")
        # The same args but with explicit types.
        builder.add(4.0, osc.OSCType.TYPE_FLOAT)
        builder.add(2, osc.OSCType.TYPE_INT)
        builder.add("value", osc.OSCType.TYPE_STRING)
        builder.add(True)
        builder.add(False)
        builder.add(b"\x01\x02\x03", osc.OSCType.TYPE_BLOB)

        # non-standard types
        builder.add("UTF текст €", osc.OSCType.TYPE_UTF8_STRING)
        builder.add(3.1415, osc.OSCType.TYPE_DOUBLE)
        builder.add(123456789, osc.OSCType.TYPE_INT64)

        args_sequence = [4.0, 2, "value", True, False, b"\x01\x02\x03",
                         4.0, 2, "value", True, False, b"\x01\x02\x03",
                         "UTF текст €", 3.1415, 123456789]

        self.assertEqual(15, len(builder.args))
        self.assertEqual("/SYNC", builder.address)

        # Test after dgram build
        builder.address = '/SEEK'
        msg = builder.build()
        self.assertEqual("/SEEK", msg.address)
        self.assertSequenceEqual(args_sequence, msg.args)

        # Test datagram parse
        from_dgram = osc.OSCMessage.parse(msg.dgram)

        self.assertEqual("/SEEK", from_dgram.address)
        self.assertSequenceEqual(args_sequence, from_dgram.args)

    def test_message_args(self):

        msg = osc.OSCMessage("/param", [5, "five", 5.5, True])

        self.assertEqual(4, len(msg.args))
        self.assertEqual([5, "five", 5.5, True], msg.args)

    def test_build_wrong_type_raises(self):
        builder = osc.OSCMessage(address="/SYNC")
        builder.add('this is not a float', osc.OSCType.TYPE_FLOAT)
        self.assertRaises(osc.OSCBuildError, builder.build)

if __name__ == "__main__":
    unittest.main()
