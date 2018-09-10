#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import unittest

try:
    from unittest import mock
except:
    import mock

import osc


class TestOSCClient(unittest.TestCase):

    @mock.patch('socket.socket')
    def test_send(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value

        msg = osc.OSCMessage(address='/')

        client = osc.OSCClient('::1', 31337)
        client.send(msg)

        self.assertTrue(mock_socket.sendto.called)
        mock_socket.sendto.assert_called_once_with(msg.build().dgram, ('::1', 31337))


if __name__ == "__main__":
    unittest.main()
