.. osc documentation master file, created by
   sphinx-quickstart on Fri Oct  2 12:17:53 2015.

Quick start
===========

Simple OSC implementation in pure Python.
Based on https://pypi.python.org/pypi/python-osc.

This library was developped following the specifications at
http://opensoundcontrol.org/spec-1_0
and is currently in a beta state.

Features
--------

* UDP client and server
* OSC arguments support - int, float, string, blob, true, false
* Blocking/threading/forking server implementations
* Simple API

Installation
------------

Download library source code and unpack in your project.
Download it here
http://bitbucket.org/grailapp/osc

After unpacking execute in terminal following command to install a library

.. code-block:: bash

    python setup.py install

Usage
-----

Examples can be found in :doc:`examples` section of this documentation.

Quick examples
--------------

.. code-block:: python

    # create osc message with address '/message/address'
    message = OSCMessage(address='/message/address')

    # argument can be string, int, float, bool and binary
    message.add( 'Some text argument' )
    message.add( 3 )
    message.add( 0.75 )
    message.add( True )

    # create osc bundle and add a message
    bundle = OSCBundle()
    bundle.add( message )

    # create client and send to 127.0.0.1:8000
    client = OSCClient('127.0.0.1', 8000)
    client.send( message )
    client.send( bundle )

    # bind server and listen for incoming messages at 127.0.0.1:8000
    server = OSCServer('127.0.0.1', 8000)
    server.serve_forever()

Table of contents
-----------------

.. toctree::
   :maxdepth: 2

   self
   classes
   examples
