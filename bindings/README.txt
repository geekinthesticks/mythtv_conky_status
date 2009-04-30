Installing the Python Bindings.
===============================

Unpack the bindings:

tar -xvzf MythTV-0.21.tar.gz

cd MythTV-0.21

sudo python setup.py install

You can check if the bindings are installed from a python shell. From
a terminal type python to enter the python shell:

ian@scamper: python
Python 2.5.2 (r252:60911, Oct  5 2008, 19:24:49)
[GCC 4.3.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>>

In the pythong shell type:

from MythTV.MythTV import *

If you don't get any errors the bindings should be installed
correctly. Type ctrl-D to exit the python shell.
