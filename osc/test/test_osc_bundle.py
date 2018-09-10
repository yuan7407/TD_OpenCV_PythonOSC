#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import unittest
import osc

_DGRAM_KNOB_ROTATES_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x14"
    b"/LFO_Rate\x00\x00\x00"
    b",f\x00\x00"
    b">\x8c\xcc\xcd")

_DGRAM_SWITCH_GOES_OFF = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"\x00\x00\x00\x00")

_DGRAM_SWITCH_GOES_ON = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

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

_DGRAM_BUNDLE_IN_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00("  # length of sub bundle: 40 bytes.
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

_DGRAM_INVALID = (
    b"#bundle\x00"
    b"\x00\x00\x00")

_DGRAM_INVALID_INDEX = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x20"
    b"/SYNC\x00\x00\x00\x00")

_DGRAM_UNKNOWN_TYPE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"iamnotaslash")


class TestOSCBundle(unittest.TestCase):

    def test_switch_goes_off(self):

        bundle = osc.OSCBundle.parse(_DGRAM_SWITCH_GOES_OFF)

        self.assertEqual(1, bundle.length)
        self.assertEqual(len(_DGRAM_SWITCH_GOES_OFF), bundle.size)
        self.assertEqual(osc.IMMEDIATELY, bundle.timestamp)

    def test_switch_goes_on(self):

        bundle = osc.OSCBundle.parse(_DGRAM_SWITCH_GOES_ON)

        self.assertEqual(1, bundle.length)
        self.assertEqual(len(_DGRAM_SWITCH_GOES_ON), bundle.size)
        self.assertEqual(osc.IMMEDIATELY, bundle.timestamp)

    def test_datagram_length(self):

        bundle = osc.OSCBundle.parse(_DGRAM_KNOB_ROTATES_BUNDLE)

        self.assertEqual(1, bundle.length)
        self.assertEqual(len(_DGRAM_KNOB_ROTATES_BUNDLE), bundle.size)
        self.assertEqual(osc.IMMEDIATELY, bundle.timestamp)

    def test_two_messages_in_bundle(self):

        bundle = osc.OSCBundle.parse(_DGRAM_TWO_MESSAGES_IN_BUNDLE)

        self.assertEqual(2, bundle.length)
        self.assertEqual(osc.IMMEDIATELY, bundle.timestamp)

        for content in bundle:
            self.assertEqual(osc.OSCMessage, type(content))

    def test_empty_bundle(self):

        bundle = osc.OSCBundle.parse(_DGRAM_EMPTY_BUNDLE)

        self.assertEqual(0, bundle.length)
        self.assertEqual(osc.IMMEDIATELY, bundle.timestamp)

    def test_bundle_in_bundle_we_must_go_deeper(self):

        bundle = osc.OSCBundle.parse(_DGRAM_BUNDLE_IN_BUNDLE)

        self.assertEqual(1, bundle.length)
        self.assertEqual(osc.IMMEDIATELY, bundle.timestamp)
        self.assertEqual(osc.OSCBundle, type(bundle[0]))

    def test_dgram_is_bundle(self):

        self.assertTrue(osc.OSCBundle.is_valid(_DGRAM_SWITCH_GOES_ON))
        self.assertFalse(osc.OSCBundle.is_valid(b'junk'))

    def test_raises_on_invalid_datagram(self):

        self.assertRaises(osc.OSCParseError, osc.OSCBundle.parse, _DGRAM_INVALID)
        self.assertRaises(osc.OSCParseError, osc.OSCBundle.parse, _DGRAM_INVALID_INDEX)

    def test_unknown_type(self):

        bundle = osc.OSCBundle.parse(_DGRAM_UNKNOWN_TYPE)

        self.assertEqual(0, bundle.length)


class TestOSCBundleBuilder(unittest.TestCase):

    def test_empty_bundle(self):

        bundle = osc.OSCBundle(timestamp=osc.IMMEDIATELY).build()

        self.assertEqual(0, bundle.length)

    def test_raises_on_build(self):

        bundle = osc.OSCBundle(timestamp=0.0)

        self.assertRaises(osc.OSCBuildError, bundle.add, None)

    def test_raises_on_invalid_timestamp(self):

        bundle = osc.OSCBundle(timestamp="I am not a timestamp")

        self.assertRaises(osc.OSCBuildError, bundle.build)

    def test_bundle_constructor(self):

        bundle = osc.OSCBundle(messages=[osc.OSCMessage('/param'), osc.OSCMessage('/param2')])

        self.assertEqual(2, bundle.length)

    def test_build_complex_bundle(self):

        bundle = osc.OSCBundle(timestamp=osc.IMMEDIATELY)
        msg = osc.OSCMessage(address="/SYNC")
        msg.add(4.0)
        # Add 4 messages in the bundle, each with more arguments.
        bundle.add(msg)
        msg.add(2)
        bundle.add(msg)
        msg.add("value")
        bundle.add(msg)
        msg.add(b"\x01\x02\x03")
        bundle.add(msg)

        sub_bundle = bundle
        # Now add the same bundle inside itself.
        bundle.add(sub_bundle)
        bundle = bundle.build()

        self.assertEqual(5, bundle.length)


if __name__ == "__main__":
    unittest.main()
