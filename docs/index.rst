.. doUtils documentation master file, created by
   sphinx-quickstart on Sun May 27 10:50:34 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

doUtils
=======

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


doUtils
=======

doUtils provides a Python module to configure and create a Digital
Ocean virtual private server ("droplet"), execute commands on it, and
transmit files to/from it.


Motivation
**********

I want to run a compute-intensive script on erratic occasions, and I
don't want it to be contending for my laptop's processing power while
I'm trying to do other stuff.

Idea: A script that provisions a temporary virtual server with the
needed packages installed, and, via script, executes the
compute-intensive job and snarf the results.


Secondary goals
###############

* Learn more about python-digitalocean, paramiko for ssh, and
  cloud-init via pyyaml.

* Don't require the big guns:  the automated provisioning /
  infrastructure configuration management tools (ansible, chef,
  puppet, et al).


Installation
************

doUtils is a set of personal tools and a learning exercise. It's
not (yet?) set up as a simple-to-install module.

You can copy the doUtils folder somewhere on your system, and put that
containing folder on your PYTHONPATH environment variable. Pipfile
lists the prerequisite packages.


Usage
*****


History
*******

* Version 0.1, June 2018. Pre-release.


License
*******

MIT



