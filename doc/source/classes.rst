.. osc documentation master file, created by
   sphinx-quickstart on Fri Oct  2 12:17:53 2015.

Classes
=======

.. automodule:: osc

OSCPacket
---------

.. autoclass:: OSCPacket
    :members:
    :special-members: __len__ __iter__ __cmp__

OSCMessage
----------

.. autoclass:: OSCMessage
    :members:
    :special-members: __len__ __iter__ __cmp__ __getitem__ __setitem__ __delitem__

OSCBundle
---------

.. autoclass:: OSCBundle
    :members:
    :special-members: __len__ __iter__ __cmp__ __getitem__ __setitem__ __delitem__

OSCServer
---------

Subclass OSCServer and override `handle` method

.. autoclass:: OSCServer
    :members: handle

OSCClient
---------

Subclass from OSCClient if you want to send something custom

.. autoclass:: OSCClient
    :members:

OSCSender
---------

.. autoclass:: OSCSender
    :members:

OSCReceiver
-----------

.. autoclass:: OSCReceiver
    :members:
