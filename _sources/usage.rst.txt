Trident Usage
=============

.. toctree::
   :maxdepth: 4
   :caption: Usage:

* ``python3 -m trident`` (Run the default configuration file using the ``TRIDENT`` section)
* ``python3 -m trident -c:s DEBUG`` (Use the `DEBUG` section in the configuration file)
* ``python3 -m trident -s:n`` (Do not store results from Trident plugins)

Arguments
---------

The arguments for Trident can also be displayed using the ``-h``, ``--help`` flag.

**Required**

* ``-c``, ``--config``
    * The path to the Trident configuration file. The config file should be of format ``.cfg``. (Default: ``config/trident.cfg``)
* ``-c:s``, ``--section``
    * The section to use in the Trident configuration file. (Default: ``TRIDENT``)

**Trident Configuration**

* ``-v``, ``--verbose``
    * Enable verbose logging of Trident
* ``-q``, ``--quiet``
    * Disable all logging of Trident
* ``-w``, ``--workers``
    * Define the amount of workers used by Trident to run plugins. If the amount of workers is set to one then Trident is run synchronously. (Default: ``1``)

**Plugin Configuration**

* ``-p:n``, ``--dont-store-on-error``
    * Do not store the accumulated results if the plugin encounters an error. Default behavior is to store the behavior up until the error occured (assuming that the plugin is using generators). (Default: ``False``)

**Storage Configuration**

* ``-s:p``, ``--path-store``
    * Define the path to where the stores are located. (Default: ``data``)

* ``-s:n``, ``--no-store``
    * Disable the storage of results for all plugins. (Default: ``False``)

* ``-s:g``, ``--global-store``
    * Define a path to a store used by all plugins. (Default: ``None``)

Configuration
-------------

Configuration of Trident is made through the configuration file, by default located at ``config/trident.cfg``.

The configuration file is divided into sections with the default section ``TRIDENT`` being used and the available parameters are the following:

* ``LOGGING_LEVEL`` (Levels: DEBUG > INFO > WARNING > ERROR > CRITICAL)
    * INFO (Display INFO and everything below it)
    * DEBUG (Displays all logging messages from `Trident`)
* ``PLUGINS`` (Defines the plugins to run in the format described below)
    * ``{"[PLUGIN_ID]": {"path": "[PATH]", "args": {"[NAME]": [VALUE]}}``
    * Where the names in the bracket are substituted for your values. The `args` section can be left out if no arguments are passed to the plugin.

Developing Plugins
------------------

Trident plugins are normal `Python` modules and the actual plugin is a class that needs to be named just as the name of the `Python` module, so if you have the plugin ``find_file.py`` then the class in the plugin needs to be named ``FindFile``.

The entry point of the plugin is always ``execute_plugin`` so when defining any new plugin this method needs to be present. See example below.

.. code-block:: python
    :linenos:
    
    class FindFile:
        def execute_plugin(self, thread_event, file_name):
            # Find the file with the name file_name on the system
            ...

Plugin Library
--------------

The Trident plugin library offers functionality to do some common operations on the host system, for example, walking the file system to find files, opening ports, sending packets and more.

The Trident plugin library uses its own library to implement crucial functionality like ``TCP``, ``UDP``, ``ICMP`` and more to not rely on external modules. These are available to anyone wishing to extend the Trident plugin library with their own functionality.

The library tries to implement each functionality using primarily generators to allows for better asynchronous behavior. For each function that return a generator there is also a iterative version that returns the finished operation, the name of the iterative version is usually the original name with ``_iter`` appended to it.

Variables
---------

By default Trident tries to pass the ``thread_event`` parameter to the plugin, this is of type ``Event`` from the ``threading`` library and is used to allow the system to halt the execution of Trident with keyboard interrupt. Note that the plugin needs to implement periodic checks of this variable using ``thread_event.is_set()`` in order for this to work. If the plugin does not implement the check then if Trident is passed an interrupt by the system then Trident will not be able to exit until the plugin operations finish.

Trident allows the user to pass any initial parameters to the plugin by defining the ``args`` key in the plugin configuration followed by the value. Trident will try to pass each variable found in the ``args`` section of the plugin configuration to the ``execute_plugin`` method, so the method needs to have these parameters defined as well.
