python-netwok-tools
===================

Tools for checking network performance between two machines, written in Python. Two types of tests are performed.

# Ping test: runs specified number of pings towards the target machine and reports the results

# File transfer test: copies an user-specified file from the ``./data`` folder to the target machine. 



Usage
-----

Sample invocation:

    $ ./network-test.py -a 161.53.68.182 -n 10 -f medfile.mp4 -l C-XI-16 -u larics -p laricsc11 

The file specified with the -f option should be placed in the ``./data`` folder.

You must have an account on the target computer. The default target folder for the file transfer is:

    /home/username/Downloads



To get help on the command-line parameters, type:

    $ ./network-test.py -h

After running the tests, please

Dependencies
------------

Paramiko

Supported platforms
-------------------

  - Linux (tested on Ubuntu 12.04 LTS)
  - Windows support is under development.