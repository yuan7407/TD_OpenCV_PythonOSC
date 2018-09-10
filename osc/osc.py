#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    osc.osc
    ~~~~~~~

    OSC protocol implementation in pure python

    :copyright: (c) 2018 by Oleksii Lytvyn.
    :license: MIT, see LICENSE for more details.
"""

import re
import time
import struct
import socket
import logging
import decimal
import datetime
import builtins
import calendar
import socketserver

__version__ = '0.6.4'
__all__ = [
    'OSCType',
    'OSCPacket',
    'OSCMessage',
    'OSCBundle',
    'OSCClient',
    'OSCServer',

    'OSCImpulse',
    'OSCColor',
    'OSCMidi',
    'IMMEDIATELY',

    'NTPError',
    'OSCParseError',
    'OSCBuildError'
    ]


class NTPError(Exception):
    """Base class for ntp errors."""


class OSCParseError(Exception):
    """Exception raised when a datagram parsing error occurs."""


class OSCBuildError(Exception):
    """Exception raised  when a datagram building error occurs."""


NTP_IMMEDIATELY = struct.pack('>q', 1)
_NTP_SYSTEM_EPOCH = datetime.date(*time.gmtime(0)[0:3])
_NTP_EPOCH = datetime.date(1900, 1, 1)
_NTP_DELTA = (_NTP_SYSTEM_EPOCH - _NTP_EPOCH).days * 24 * 3600


def ntp_to_time(date):
    """Convert a NTP time to system time.
    System time is represented by seconds since the epoch in UTC.

    Args:
        date: NTP time to be converted
    Returns:
        system time in seconds
    """

    return date - _NTP_DELTA


def time_to_ntp(date):
    """Convert a system time to a NTP time datagram.
    System time is represented by seconds since the epoch in UTC.

    Args:
        date: System time to be converted
    Returns:
        NTP time in seconds
    Raises:
        NTPError if date is invalid
    """
    try:
        ntp = date + _NTP_DELTA
    except TypeError as e:
        raise NTPError("Invalid date: %s" % e)

    num_secs, fraction = str(ntp).split('.')

    return struct.pack('>I', int(num_secs)) + struct.pack('>I', int(fraction))


IMMEDIATELY = 0

_INT_DGRAM_LEN = 4
_UINT_DGRAM_LEN = 4
_BLOB_DGRAM_PAD = 4
_FLOAT_DGRAM_LEN = 4
_STRING_DGRAM_PAD = 4
_TIMETAG_DGRAM_LEN = _INT_DGRAM_LEN * 2
_COLOR_DGRAM_LEN = 4
_MIDI_DGRAM_LEN = 4
_DOUBLE_DGRAM_LEN = 8
_INT64_DGRAM_LEN = 8
_CHAR_DGRAM_LEN = 4


class OSCImpulse(object):
    """Representation of Impulse OSC type"""

    pass


class OSCMidi(object):
    """Representation of OSC OSCMidi message"""

    def __init__(self, port, status, data1=None, data2=None):
        self.port = port
        self.status = status
        self.data1 = data1
        self.data2 = data2

    def pack(self):
        """Returns midi message representation"""
        return struct.pack('>BBBB', self.port, self.status, self.data1, self.data2)

    @classmethod
    def unpack(cls, data):
        """Parse datagram into OSCMidi instance

        Args:
            data (bytes): datagram

        Returns:
            OSCMidi instance
        """
        return cls(*struct.unpack('>BBBB', data))


class OSCColor(object):
    """Representation of OSC color type in RGBA format"""

    __slots__ = 'r', 'g', 'b', 'a'

    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def pack(self):
        """Returns datagram of OSCColor type"""

        return struct.pack('>BBBB', self.r, self.g, self.b, self.a)

    @classmethod
    def unpack(cls, data):
        """Parse datagram into OSCColor instance

        Args:
            data (bytes): datagram

        Returns:
            OSCColor instance
        """

        return cls(*struct.unpack('>BBBB', data))


class OSCType(object):
    """Reading and writing OSC types"""

    TYPE_INT = 'i'
    TYPE_UINT = 'u'
    TYPE_CHAR = 'c'
    TYPE_BLOB = 'b'
    TYPE_MIDI = 'm'
    TYPE_NULL = 'N'
    TYPE_TRUE = 'T'
    TYPE_FALSE = 'F'
    TYPE_FLOAT = 'f'
    TYPE_COLOR = 'r'
    TYPE_STRING = 's'
    TYPE_IMPULSE = 'I'
    TYPE_TIMETAG = 't'
    TYPE_DOUBLE = 'd'
    TYPE_INT64 = 'h'
    TYPE_UTF8_STRING = 'S'

    # list of all supported types
    _SUPPORTED_TYPES = (
        TYPE_INT,
        TYPE_UINT,
        TYPE_CHAR,
        TYPE_BLOB,
        TYPE_MIDI,
        TYPE_NULL,
        TYPE_TRUE,
        TYPE_FALSE,
        TYPE_FLOAT,
        TYPE_COLOR,
        TYPE_STRING,
        TYPE_IMPULSE,
        TYPE_TIMETAG,

        TYPE_INT64,
        TYPE_DOUBLE,
        TYPE_UTF8_STRING
        )

    # map of types and corresponding io methods
    TYPES_MAP = {
        TYPE_INT: 'int',
        TYPE_UINT: 'uint',
        TYPE_CHAR: 'char',
        TYPE_BLOB: 'blob',
        TYPE_MIDI: 'midi',
        TYPE_FLOAT: 'float',
        TYPE_COLOR: 'color',
        TYPE_STRING: 'string',
        TYPE_TIMETAG: 'timetag',
        TYPE_DOUBLE: 'double',
        TYPE_INT64: 'int64',
        TYPE_UTF8_STRING: 'utf8_string'
        }

    @classmethod
    def is_supported(cls, _type):
        """Check if given type is supported

        Args:
            _type (str): OSC type tag
        """

        return _type in cls._SUPPORTED_TYPES

    @classmethod
    def tag(cls, value):
        """Get OSC type tag for `value` argument

        Args:
            value: argument value

        Returns:
            OSC type tag
        """

        builtin_type = type(value)
        arg_type = cls.TYPE_NULL

        if builtin_type == builtins.str:
            arg_type = cls.TYPE_STRING
        elif builtin_type == builtins.bytes:
            arg_type = cls.TYPE_BLOB
        elif builtin_type == builtins.int:
            arg_type = cls.TYPE_INT
        elif builtin_type == builtins.float:
            arg_type = cls.TYPE_FLOAT
        elif builtin_type == builtins.bool and value:
            arg_type = cls.TYPE_TRUE
        elif builtin_type == builtins.bool and not value:
            arg_type = cls.TYPE_FALSE
        elif value == None:
            arg_type = cls.TYPE_NULL
        elif builtin_type == builtins.str and len(value) == 1:
            arg_type = cls.TYPE_CHAR
        elif isinstance(value, OSCColor):
            arg_type = cls.TYPE_COLOR
        elif isinstance(value, OSCMidi):
            arg_type = cls.TYPE_MIDI
        elif isinstance(value, OSCImpulse):
            arg_type = cls.TYPE_IMPULSE

        return arg_type

    @classmethod
    def has_datagram(cls, _type):
        """Check if this type has i/o method

        Args:
            _type (str): OSC type tag
        Returns
            True if type has datagram processing method
        """

        return _type in cls.TYPES_MAP

    @classmethod
    def type(cls, _type, data, index=-1):
        """Read and write any supported OSC type

        Args:
            _type (str): OSC type tag
            data (bytes, object): datagram or value to be converted
            index (int): index from which type datagram starts in datagram given
        Returns:
            Datagram from value given if `index` is -1, otherwise parse datagram into value
        """

        return getattr(cls, cls.TYPES_MAP[_type])(data, index)

    @classmethod
    def string(cls, data, index=-1):
        """Get a python string from the datagram and vice versa

        According to the specifications, a string is:
        "A sequence of non-null ASCII characters followed by a null,
        followed by 0-3 additional null characters to make the total number
        of bits a multiple of 32".

        Args:
            data: A datagram packet or value to be converted
            index: An index where the string starts in the datagram.
        Returns:
            A tuple containing the string and the new end index.
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if datagram could not be build.
        """

        # read
        if index != -1:
            offset = 0

            try:
                while data[index + offset] != 0:
                    offset += 1

                if offset == 0:
                    raise OSCParseError("OSC string cannot begin with a null byte: %s" % data[index:])

                if offset % _STRING_DGRAM_PAD == 0:
                    offset += _STRING_DGRAM_PAD
                else:
                    offset += (-offset % _STRING_DGRAM_PAD)

                if offset > len(data[index:]):
                    raise OSCParseError("Datagram is too short")

                data_str = data[index:index + offset]

                return data_str.replace(b'\x00', b'').decode('ascii'), index + offset
            except (IndexError, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                dgram = data.encode('ascii')  # Default, but better be explicit.
            except (UnicodeEncodeError, AttributeError) as e:
                raise OSCBuildError("Incorrect string, could not encode %s" % e)

            diff = _STRING_DGRAM_PAD - (len(dgram) % _STRING_DGRAM_PAD)
            dgram += (b'\x00' * diff)

            return dgram

    @classmethod
    def utf8_string(cls, data, index=-1):
        """Get a python string from the datagram and vice versa
        Like OSC string but in UTF-8 encoding

        Args:
            data: A datagram packet or value to be converted
            index: An index where the string starts in the datagram.
        Returns:
            A tuple containing the string and the new end index.
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if datagram could not be build.
        """

        # read
        if index != -1:
            offset = 0

            try:
                while data[index + offset] != 0:
                    offset += 1

                if offset == 0:
                    raise OSCParseError("OSC string cannot begin with a null byte: %s" % data[index:])

                if offset % _STRING_DGRAM_PAD == 0:
                    offset += _STRING_DGRAM_PAD
                else:
                    offset += (-offset % _STRING_DGRAM_PAD)

                if offset > len(data[index:]):
                    raise OSCParseError("Datagram is too short")

                data_str = data[index:index + offset]

                return data_str.replace(b'\x00', b'').decode('utf-8'), index + offset
            except (IndexError, TypeError) as ex:
                raise OSCParseError("Could not parse datagram %s" % ex)
        # write
        else:
            try:
                dgram = data.encode('utf-8')
            except (UnicodeEncodeError, AttributeError) as e:
                raise OSCBuildError("Incorrect string, could not encode %s" % e)

            diff = _STRING_DGRAM_PAD - (len(dgram) % _STRING_DGRAM_PAD)
            dgram += (b'\x00' * diff)

            return dgram

    @classmethod
    def int(cls, data, index=-1):
        """Returns the datagram for the given integer parameter value
        Get a 32-bit big-endian two's complement integer from the datagram

        Args:
            data: A datagram packet or value to be converted
            index: An index where the integer starts in the datagram.
        Returns:
            Datagram of value given if `index` is -1 otherwise
            tuple containing the integer and the new end index.
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if the int could not be converted.
        """

        # read
        if index != -1:
            try:
                if len(data[index:]) < _INT_DGRAM_LEN:
                    raise OSCParseError("Datagram is too short")
                return struct.unpack('>i', data[index:index + _INT_DGRAM_LEN])[0], index + _INT_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return struct.pack('>i', data)
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def uint(cls, data, index=-1):
        """Returns the datagram for the given integer parameter value
        Get a 32-bit big-endian unsigned integer from the datagram

        Args:
            data: A datagram packet or value to be converted
            index: An index where the integer starts in the datagram.
        Returns:
            Datagram of value given if `index` is -1 otherwise
            tuple containing the integer and the new end index.
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if the int could not be converted.
        """

        # read
        if index != -1:
            try:
                if len(data[index:]) < _UINT_DGRAM_LEN:
                    raise OSCParseError("Datagram is too short")
                return struct.unpack('>I', data[index:index + _UINT_DGRAM_LEN])[0], index + _UINT_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return struct.pack('>I', data)
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def int64(cls, data, index=-1):
        """Read and write Int64 from OSC message

        Args:
            data: integer or datagram
            index: An index where the integer starts in the datagram.
        Returns:
            Datagram of int64 if `index` is -1
            Integer parsed from datagram otherwise
        Raises:
            OSCBuildError if data can't be written
            OSCParseError if data could not be parsed from datagram
        """

        # read
        if index != -1:
            try:
                return struct.unpack('>q', data[index:index + _INT64_DGRAM_LEN])[0], index + _INT64_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return struct.pack('>q', data)
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def double(cls, data, index=-1):
        """Read and write OSC double datagram

        Args:
            data: double or datagram of it
            index: An index where the double starts in the datagram.
        Returns:
            Double datagram if `index` is -1
            Double value and next index
        Raises:
            OSCBuildError if `data` can't be packed
            OSCParseError if `data` could not be parsed
        """

        # read
        if index != -1:
            try:
                return struct.unpack('>d', data[index:index + _DOUBLE_DGRAM_LEN])[0], index + _DOUBLE_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return struct.pack('>d', data)
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: {}".format(e))

    @classmethod
    def float(cls, data, index=-1):
        """Get a 32-bit big-endian IEEE 754 floating point number from the datagram.
        Returns the datagram for the given float parameter value if `index` is -1

        Args:
            data: A datagram packet of value to be converted
            index: An index where the float starts in the datagram.
        Returns:
            A tuple containing the float and the new end index if `index` != -1
            Datagram of float value if `index` is -1
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if the float could not be converted.
        """

        # read
        if index != -1:

            try:
                if len(data[index:]) < _FLOAT_DGRAM_LEN:
                    data += b'\x00' * (_FLOAT_DGRAM_LEN - len(data[index:]))

                return struct.unpack('>f', data[index:index + _FLOAT_DGRAM_LEN])[0], index + _FLOAT_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return struct.pack('>f', data)
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def timetag(cls, data, index=-1):
        """Get a 64-bit big-endian fixed-point time tag as a date from the datagram.
        Create time tag datagram if `index` is -1

        According to the specifications, a date is represented as is:
        "the first 32 bits specify the number of seconds since midnight on
        January 1, 1900, and the last 32 bits specify fractional parts of a second
        to a precision of about 200 picoseconds".

        Args:
            data: A datagram packet or time value
            index: An index where the date starts in the datagram.
        Returns:
            A tuple containing the system date and the new end index.
            returns IMMEDIATELY (0) if the corresponding OSC sequence was found.
            Create time tag datagram if `index` is -1
        Raises:
            OSCParseError if the datagram could not be parsed.
            NTPError if time cant be converted
        """
        # read
        if index != -1:
            # Check for the special case first.
            if data[index:index + _TIMETAG_DGRAM_LEN] == NTP_IMMEDIATELY:
                return IMMEDIATELY, index + _TIMETAG_DGRAM_LEN

            if len(data[index:]) < _TIMETAG_DGRAM_LEN:
                raise OSCParseError("Datagram is too short")

            num_secs, index = OSCType.int(data, index)
            fraction, index = OSCType.int(data, index)
            # Get a decimal representation from those two values.
            dec = decimal.Decimal(str(num_secs) + '.' + str(fraction))
            # And convert it to float simply.
            system_time = float(dec)

            return ntp_to_time(system_time), index
        # write
        else:
            if data == IMMEDIATELY:
                return NTP_IMMEDIATELY

            try:
                return time_to_ntp(data)
            except NTPError as error:
                raise OSCBuildError(error)

    @classmethod
    def color(cls, data, index=-1):
        """Read and write OSCColor OSC type

        Args:
            data (bytes, OSCColor): datagram or OSCColor instance
            index: An index where the type starts in the datagram.
        Returns:
            OSCColor instance if index given
            Datagram for OSCColor instance if `index` is -1
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if datagram for OSCMidi message can't be created
        """

        # read
        if index != -1:
            try:
                return OSCColor.unpack(data[index:index + _COLOR_DGRAM_LEN]), index + _COLOR_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return data.pack()
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def midi(cls, data, index=-1):
        """Read and write OSC OSCMidi message

        Args:
            data: OSCMidi instance or datagram to be parsed
            index: An index where the type starts in the datagram.
        Returns:
            OSCMidi message datagram if `index` is -1
            OSCMidi instance otherwise
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if datagram for OSCMidi message can't be created
        """

        # read
        if index != -1:
            try:
                return OSCMidi.unpack(data[index:index + _MIDI_DGRAM_LEN]), index + _MIDI_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return data.pack()
            except struct.error as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def char(cls, data, index=-1):
        """Read and write Char OSC type

        Args:
            data: Datagram or char
            index: An index when data starts in datagram
        Returns:
            Char if `index` was given
            Datagram if `index` is -1
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if datagram can't be created
        """

        # read
        if index != -1:
            try:
                return data[index].decode('ascii'), index + _CHAR_DGRAM_LEN
            except (struct.error, TypeError) as e:
                raise OSCParseError("Could not parse datagram %s" % e)
        # write
        else:
            try:
                return struct.pack('>c', data.encode('ascii')) + b'\x00' * 3
            except (struct.error, UnicodeEncodeError) as e:
                raise OSCBuildError("Wrong argument value passed: %s" % e)

    @classmethod
    def blob(cls, data, index=-1):
        """Get a blob from the datagram if index given otherwise
        returns the datagram for the given `data` value.

        According to the specifications, a blob is made of
        "an int32 size count, followed by that many 8-bit bytes of arbitrary
        binary data, followed by 0-3 additional zero bytes to make the total
        number of bits a multiple of 32".

        Args:
            data: A datagram packet.
            index: An index where the float starts in the datagram.
        Returns:
            A tuple containing the blob and the new end index if index was given
            Datagram of blob `data` if `index` is -1
        Raises:
            OSCParseError if the datagram could not be parsed.
            OSCBuildError if the value was empty or if its size didn't fit an OSC int.
        """

        # read
        if index != -1:
            size, offset = OSCType.int(data, index)
            # Make the size a multiple of 32 bits.
            total_size = size + (-size % _BLOB_DGRAM_PAD)
            end_index = offset + size

            if end_index - index > len(data[index:]):
                raise OSCParseError("Datagram is too short.")

            return data[offset:offset + size], offset + total_size
        # write
        else:
            val = data

            if not val:
                raise OSCBuildError("Blob value cannot be empty")

            dgram = OSCType.int(len(val)) + val

            while len(dgram) % _BLOB_DGRAM_PAD != 0:
                dgram += b'\x00'

            return dgram


class OSCPacket(object):
    """Unit of transmission of the OSC protocol.

    Any application that sends OSC Packets is an OSC Client.
    Any application that receives OSC Packets is an OSC Server.
    """

    def __init__(self, dgram):
        """Initialize an OSCPacket with the given UDP datagram.

        Args:
            dgram: the raw UDP datagram holding the OSC packet.
        Raises:
            OSCParseError if the datagram could not be parsed.
        """

        self.time = calendar.timegm(time.gmtime())
        self.dgram = dgram
        self.message = None

        try:
            if OSCBundle.is_valid(dgram):
                self.message = OSCBundle.parse(dgram)
            elif OSCMessage.is_valid(dgram):
                self.message = OSCMessage.parse(dgram)
            else:
                # Empty packet, should not happen as per the spec but heh, UDP...
                raise OSCParseError("OSC Packet should at least contain an OSCMessage or an OSCBundle.")
        except OSCParseError as e:
            raise OSCParseError("Could not parse packet: %s" % e)

    def __cmp__(self, other):
        """Compare two OSCPacket's

        Args:
            other (OSCPacket): other OSCPacket to compare
        Returns:
            True if two OSCPacket's is the same
        """

        return self.dgram == other.dgram

    @property
    def size(self):
        """Size of datagram"""

        return len(self.dgram)


class OSCMessage(object):
    """Builds arbitrary OSCMessage instances."""

    def __init__(self, address="/", args=None):
        """Initialize a new OSCMessage.

        Args:
            address (str): The osc address to send this message to.
            args (list): list of args to add to message
        """

        self._address = "/"
        self._args = []
        self._dgram = b''

        # OSC address will be checked here
        self.address = address

        if args and len(args) > 0:
            for value in args:
                self.add(value)

    def __iter__(self):
        """Returns an iterator over the arguments of this message in pairs (osc type tag, value)"""

        return iter(self._args)

    def __len__(self):
        """Returns length of arguments"""

        return len(self._args)

    def __getitem__(self, key):
        """Get a OSCMessage argument by index

        Args:
            key (int): index of argument
        Returns:
            argument of OSCMessage
        Raises:
            IndexError if index out of range
        """

        if key >= len(self._args):
            raise IndexError("Index out of range.")

        return self._args[key]

    def __setitem__(self, key, value):
        """Set argument by index, if key is greater than
        length of arguments error will be raised

        Args:
            key (int): index of argument
            value: an argument
        Raises:
            IndexError if there is no argument with this index
        """

        if key >= len(self._args):
            raise IndexError("Index out of range.")
        else:
            arg_type = OSCType.tag(value)
            self._args[key] = (arg_type, value)

    def __delitem__(self, key):
        """Delete argument by index

        Args:
            key (int): index of argument
        Raises:
            IndexError if there is no argument with this index
        """

        if key >= len(self._args):
            raise IndexError("Index out of range.")

        del self._args[key]

    def __contains__(self, value):
        """Returns True if value in arguments list

        Args:
            value: argument value
        """

        return self.index(value) >= 0

    def __cmp__(self, other):
        """Check two OSCMessage's to be equal

        Args:
            other (OSCMessage): other OSCMessage
        Returns:
            True if two messages equals
        """

        return self.build().dgram == other.build().dgram

    @property
    def address(self):
        """Returns the OSC address this message will be sent to."""

        return self._address

    @address.setter
    def address(self, value):
        """Sets the OSC address this message will be sent to.

        Args:
            value (str): OSC message address pattern
        """

        if not value.startswith('/'):
            raise ValueError("Given '%s' OSC address doesn't start with /." % str(value))
        elif not self.is_valid_address(value):
            raise ValueError("Given '%s' OSC address doesn't matches with valid address pattern." % str(value))

        self._address = value

    @property
    def args(self):
        """Returns list of value added as arguments"""

        return [a[1] for a in self._args]

    @property
    def size(self):
        """Returns length of the datagram for this message."""

        return len(self._dgram)

    @property
    def dgram(self):
        """Returns datagram from which this message was built."""

        return self._dgram

    def add(self, value, _type=None):
        """Add a typed argument to this message.

        Args:
            value: The corresponding value for the argument.
            _type: A value in ARG_TYPE_* defined in this class,
                if none then the type will be guessed.
        Raises:
            ValueError: if the type is not supported.
        """

        self.append(value, _type)

    def append(self, value, _type=None):
        """Add a typed argument to this message.

        Args:
            value: The corresponding value for the argument.
            _type: A value in ARG_TYPE_* defined in this class,
                if none then the type will be guessed.
        Raises:
            ValueError: if the type is not supported.
        """

        if _type and not OSCType.is_supported(_type):
            raise ValueError("Type is not supported, %s was given." % str(_type))

        if not _type:
            _type = OSCType.tag(value)

        self._args.append((_type, value))

    def extend(self, values):
        """Extend arguments list, all values will be added using auto type

        Args:
            values (list): a list of values
        """

        for value in values:
            self.append(value)

    def insert(self, index, value, _type=None):
        """Insert typed argument at specific index

        Args:
            index (int): index of insertion
            value: The corresponding value for the argument.
            _type: A value in ARG_TYPE_* defined in this class,
                if none then the type will be guessed.
        Raises:
            ValueError: if the type is not supported.
            IndexError: if index is greater than list size
        """

        if index >= len(self._args):
            raise IndexError("Index is out of range.")

        if _type and not OSCType.is_supported(_type):
            raise ValueError("Type is not supported, %s was given." % str(_type))

        if not _type:
            _type = OSCType.tag(value)

        self._args.insert(index, (_type, value))

    def remove(self, value):
        """Remove the first item from the arguments list whose value is `value`.

        Args:
            value: argument value
        Raises:
            ValueError: if value is not fund in arguments list
        """

        index = self.index(value)

        if (index > 0) and (index < len(self._args)):
            del self._args[index]
        else:
            raise ValueError("Item not found in arguments list.")

    def index(self, value, start=0, end=False):
        """Find value in arguments list and return first index otherwise return -1.
        The returned index is computed relative to the beginning of the full sequence rather than the start argument.
        """
        found_index = -1

        if not end:
            end = len(self._args)

        for index, arg in enumerate(self._args):

            if index < start:
                continue

            if index >= end:
                break

            if value == arg[1]:
                found_index = index

        return found_index

    def clear(self):
        """Remove all arguments from message"""

        self._args.clear()

    def copy(self):
        """Create copy of OSCMessage

        Returns:
            New OSCMessage instance
        """
        self.build()

        return OSCMessage.parse(self._dgram)

    def build(self):
        """Builds OSCMessage datagram and return current instance

        Returns:
            an OSCMessage instance.
        Raises:
            OSCBuildError: if the message could not be build or if the address was empty.
        """

        if not self._address:
            raise OSCBuildError("OSC addresses cannot be empty")

        dgram = b''

        try:
            # Write the address.
            dgram += OSCType.string(self._address)

            if not self._args:
                self._dgram = dgram

                return self

            # Write the parameters.
            types = "".join([arg[0] for arg in self._args])
            dgram += OSCType.string(',' + types)

            for _type, value in self._args:
                # if type in list use function to create datagram
                if OSCType.has_datagram(_type):
                    dgram += OSCType.type(_type, value)
                # process arg without datagram
                elif OSCType.is_supported(_type):
                    continue
                # otherwise type not supported
                else:
                    raise OSCBuildError("Incorrect parameter type found %s" % str(_type))

            self._dgram = dgram

            return self
        except OSCBuildError as e:
            raise OSCBuildError("Could not build the message: %s" % str(e))

    def _parse(self, dgram):
        """Parse datagram

        Args:
            dgram (bytes): datagram of OSCMessage
        """

        self._dgram = dgram

        try:
            self._address, index = OSCType.string(self._dgram, 0)

            if not self._dgram[index:]:
                # No params is legit, just return now.
                return

            # Get the parameters types.
            typetag, index = OSCType.string(self._dgram, index)

            if typetag.startswith(','):
                typetag = typetag[1:]

            # Parse each parameter given its type.
            for _type in typetag:

                if OSCType.has_datagram(_type):
                    value, index = OSCType.type(_type, self._dgram, index)
                elif _type == OSCType.TYPE_TRUE:
                    value = True
                elif _type == OSCType.TYPE_FALSE:
                    value = False
                elif _type == OSCType.TYPE_NULL:
                    value = None
                elif _type == OSCType.TYPE_IMPULSE:
                    value = OSCImpulse()
                else:
                    logging.warning("Unhandled parameter type: {0}".format(_type))
                    continue

                self._args.append((_type, value))
        except OSCParseError as e:
            raise OSCParseError("Found incorrect datagram, ignoring it: %s" % e)

    @staticmethod
    def parse(dgram):
        """Create OSCMessage from datagram

        Args:
            dgram (bytes): from what to build OSCMessage
        Returns:
            OSCMessage parsed from datagram
        """

        message = OSCMessage()
        message._parse(dgram)

        return message

    @staticmethod
    def is_valid(dgram):
        """Check datagram to be valid OSCMessage

        Args:
            dgram (bytes): datagram os of OSCMessage
        Returns:
            whether this datagram starts as an OSC message.
        """

        return dgram.startswith(b'/')

    @staticmethod
    def is_valid_address(address):
        """Check if given value is valid OSC-string address pattern

        Args:
            address (str): OSC address pattern
        Returns:
            True if valid
        """

        return address == '/' or re.compile("^/[a-zA-Z0-9/_\-?*\[\]]+").match(address)


class OSCBundle(object):
    """Builds arbitrary OSCBundle instances."""

    _BUNDLE_PREFIX = b"#bundle\x00"

    def __init__(self, timestamp=IMMEDIATELY, messages=None):
        """Build a new bundle with the associated timestamp.

        Args:
            timestamp (int): system time represented as a floating point number of
                       seconds since the epoch in UTC or IMMEDIATELY.
            messages (list): List of OSCMessage's to add to bundle
        """

        self._timestamp = timestamp
        self._contents = []
        self._dgram = b''

        if messages and len(messages) > 0:
            for value in messages:
                self.add(value)

    def __iter__(self):
        """Returns an iterator over the bundle's content."""

        return iter(self._contents)

    def __len__(self):
        """Returns length of contents"""

        return len(self._contents)

    def __getitem__(self, key):
        """Get item from OSCBundle by index

        Args:
            key (int): index of item
        Returns:
            item from contents
        """

        return self._contents[key]

    def __setitem__(self, key, value):
        """Set item of OSCBundle

        Args:
            key (int): index of item
            value (OSCBundle, OSCMessage): an OSCBundle or OSCMessage
        """

        if key >= len(self._contents):
            raise IndexError("Index out of range.")

        if not isinstance(value, OSCBundle) or not isinstance(value, OSCMessage):
            raise TypeError("Type of assigned values is not OSCBundle or OSCMessage.")

        self._contents[key] = value

    def __delitem__(self, key):
        """Remove item from bundle

        Args:
            key (int): index of item
        """

        if key >= len(self._contents):
            raise IndexError("Index out of range.")

        del self._contents[key]

    def __contains__(self, item):
        """Check if OSCMessage in bundle

        Returns:
            returns True if item in this bundle
        """

        return item in self._contents

    def __cmp__(self, other):
        """Compare two bundles

        Args:
            other (OSCBundle): other bundle to compare
        """

        return self.dgram == other.dgram

    @property
    def timestamp(self):
        """Returns timestamp associated with this bundle."""

        return self._timestamp

    @property
    def length(self):
        """Returns number of messages in bundle."""

        return len(self._contents)

    @property
    def size(self):
        """Returns length of the datagram for this bundle."""

        return len(self._dgram)

    @property
    def dgram(self):
        """Returns datagram from which this bundle was built."""

        return self._dgram

    def append(self, content):
        """Add a new content to this bundle.

        Args:
            content: Either an OSCBundle or an OSCMessage
        Raises:
            OSCBuildError: if we could not build the bundle.
        """

        if isinstance(content, OSCMessage) or isinstance(content, OSCBundle):
            self._contents.append(content.build())
        else:
            raise OSCBuildError("Content must be either OSCBundle or OSCMessage found %s" % type(content))

    def add(self, content):
        """Same as append method"""

        self.append(content)

    def build(self):
        """Build an OSCBundle with the current state of this builder.

        Raises:
            OSCBuildError: if we could not build the bundle.
        """

        dgram = b'' + self._BUNDLE_PREFIX

        try:
            dgram += OSCType.timetag(self._timestamp)

            for content in self._contents:
                if isinstance(content, OSCMessage) or isinstance(content, OSCBundle):
                    size = content.size
                    dgram += OSCType.int(size)
                    dgram += content.dgram
                else:
                    raise OSCBuildError(
                        "Content must be either OSCBundle or OSCMessage found %s" % type(content))

            return OSCBundle.parse(dgram)
        except OSCBuildError as e:
            raise OSCBuildError("Could not build the bundle %s" % e)

    def _parse(self, dgram):
        """Parse datagram and fill contents of this OSCBundle

        Args:
            dgram (bytes): datagram of OSCBundle
        """

        # Interesting stuff starts after the initial b"#bundle\x00".
        self._dgram = dgram
        index = len(self._BUNDLE_PREFIX)

        try:
            self._timestamp, index = OSCType.timetag(self._dgram, index)
        except OSCParseError as e:
            raise OSCParseError("Could not get the date from the datagram: %s" % e)

        # Get the contents as a list of OSCBundle and OSCMessage.
        self._contents = self._parse_contents(index)

    def _parse_contents(self, index):
        """Parse datagram into OSCBundle

        Args:
            index (int): start index of next OSCMessage in bundle
        Raises:
            OSCParseError: if we could not parse the bundle.
        """

        contents = []

        try:
            # An OSC Bundle Element consists of its size and its contents.
            # The size is an int32 representing the number of 8-bit bytes in the
            # contents, and will always be a multiple of 4. The contents are either
            # an OSC Message or an OSC Bundle.
            while self._dgram[index:]:
                # Get the sub content size.
                content_size, index = OSCType.int(self._dgram, index)
                # Get the datagram for the sub content.
                content_dgram = self._dgram[index:index + content_size]
                # Increment our position index up to the next possible content.
                index += content_size
                # Parse the content into an OSC message or bundle.
                if OSCBundle.is_valid(content_dgram):
                    contents.append(OSCBundle.parse(content_dgram))
                elif OSCMessage.is_valid(content_dgram):
                    contents.append(OSCMessage.parse(content_dgram))
                else:
                    logging.warning("Could not identify content type of dgram %s" % content_dgram)
        except (OSCParseError, IndexError) as e:
            raise OSCParseError("Could not parse a content datagram: %s" % e)

        return contents

    @classmethod
    def is_valid(cls, dgram):
        """Returns whether this datagram starts like an OSC bundle.

        Args:
            dgram: datagram of OSCBundle
        Returns:
            weather datagram is OSCBundle
        """

        return dgram.startswith(cls._BUNDLE_PREFIX)

    @staticmethod
    def parse(dgram):
        """Parse OSCBundle from datagram

        Args:
            dgram: datagram of OSCBundle
        Returns:
            OSCBundle instance
        """

        bundle = OSCBundle()
        bundle._parse(dgram)

        return bundle


class OSCClient(object):
    """Send OSCMessage's and OSCBundle's to multiple servers"""

    def __init__(self, address="127.0.0.1", port=False):
        """Initialize the client.

        Args:
            address (str): recipient ip address
            port (int): recipient port
        """

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        self._clients = []
        self._closed = False

        if address and port:
            self.add(address, port)

    def __len__(self):
        """Returns number of clients"""

        return len(self._clients)

    def __bool__(self):
        """Returns True if at least one client is available"""

        return len(self) > 0

    @property
    def clients(self):
        """Returns list of receipts"""

        return self._clients

    def add(self, address, port):
        """Add a recipient

        Args:
            address (str): ip address of server
            port (int): port of server
        Raises:
            ValueError if one of arguments is invalid
        """

        if not isinstance(address, str):
            raise ValueError("Given address is not a string")

        if not isinstance(port, int) or port <= 0:
            raise ValueError("Given port number is not int or invalid")

        self._clients.append((address, port))

    def remove(self, address, port):
        """Remove a recipient

        Args:
            address (str): ip address of server
            port (int): port of server
        """

        for client in self._clients:
            if client[0] == address and client[1] == port:
                self._clients.remove(client)

                break

    def clear(self):
        """Clear list of receipts"""

        self._clients = []

    def send(self, message):
        """Sends an OSCBundle or OSCMessage to the servers.

        Args:
            message (OSCMessage, OSCBundle): a OSCMessage or OSCBundle to send
        """

        if not (isinstance(message, OSCMessage) or isinstance(message, OSCBundle)):
            raise ValueError("Given message is not a OSCMessage or OSCBundle")

        # create new socket if previously closed
        if self._closed:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setblocking(0)
            self._closed = False

        dgram = message.build().dgram

        for address in self._clients:
            self._socket.sendto(dgram, address)

    def close(self):
        """Close socket connection"""

        if not self._closed:
            self._socket.close()
            self._closed = True


class _UDPRequestHandler(socketserver.BaseRequestHandler):
    """Handles correct UDP messages for all types of server.

    Whether this will be run on its own thread, the server's or a whole new
    process depends on the server you instantiated, look at their documentation.

    This method is called after a basic sanity check was done on the datagram,
    basically whether this datagram looks like an osc message or bundle,
    if not the server won't even bother to call it and so no new
    threads/processes will be spawned.
    """

    def handle(self):
        """Handle UDP request and call handler callback"""

        data = self.request[0]
        callback = self.server.handle

        # Get OSC messages from all bundles or standalone message.
        try:
            packet = OSCPacket(data)
            now = calendar.timegm(time.gmtime())

            # If the message is to be handled later, then so be it.
            if packet.time > now:
                time.sleep(packet.time - now)

            callback(self.client_address, packet.message, packet.time)
        except OSCParseError:
            logging.warning("OSCParseError: Could not parse OSC packet")


class OSCServer(socketserver.UDPServer):
    """Superclass for different flavors of OSCServer

    You can change server logic by extending from both
    OSCServer and socketserver.ThreadingMixIn or socketserver.ForkingMixIn
    """

    def __init__(self, address="127.0.0.1", port=9000):
        """Initialize OSCServer class

        Args:
            address (string): string representation of ip address, for example: 127.0.0.1
            port (int): port of server
        """

        super(OSCServer, self).__init__((address, port), _UDPRequestHandler)

    def verify_request(self, request, client_address):
        """Returns true if the data looks like a valid OSC UDP datagram.

        Args:
            request: A request data
            client_address: Client address
        Returns:
            True if request is valid
        """

        data = request[0]

        return OSCBundle.is_valid(data) or OSCMessage.is_valid(data)

    def server_bind(self):
        """Called by constructor to bind the socket."""

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

    def handle(self, address, message, date):
        """Handle receiving of OSCMessage or OSCBundle

        Args:
            address: typle (host, port)
            message: OSCMessage or OSCBundle
            date: int number which represents time of message
        Raises:
            NotImplementedError if you don't override it
        """

        raise NotImplementedError("Re-implement this method")
