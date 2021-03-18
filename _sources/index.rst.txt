Trident Asynchronous Monitor
============================

**Trident** is a asynchronous monitor environment that allows for defining and running [plugins](#plugins) to scan/modify/store resources on the system. `Trident` comes pre-packaged with some [plugins](#plugins) to function as a monitor on the system.

Trident currently allows for modules written in `Python` to act as plugins using the Trident library to allow for some basic instructions.

Trident tries to use as little external modules as possible and allows the user to run Trident using only the standard library. This is done to ensure maximum compatability with hosts and to allow to focus on developing asynchronous libraries to use in the plugins. Trident also has the ability to use methods that rely on external libraries as well, like `requests <https://requests.readthedocs.io/en/master/>`_ if preferred, for example, if the user lacks required functionality in the Trident plugin library functions.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   trident/lib

Trident Usage
=============

.. toctree::
   :maxdepth: 4
   :caption: Usage:

   usage


Trident Source
==============

.. toctree::
   :maxdepth: 4
   :caption: Trident Source

   github