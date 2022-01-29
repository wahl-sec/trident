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
    * The path to the Trident configuration file. The config file should be of format ``.json``. (Default: ``config/trident.json``)
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
* ``-p:f``, ``--filter-results``
    * Only store the values matching the filter of the form of regular expressions. (Default: ``[]``)

**Storage Configuration**

* ``-s:p``, ``--path-store``
    * Define the path to where the stores are located. (Default: ``data``)

* ``-s:n``, ``--no-store``
    * Disable the storage of results for all plugins. (Default: ``False``)

* ``-s:g``, ``--global-store``
    * Define a path to a store used by all plugins. (Default: ``None``)

**Checkpoint Configuration**

* ``-c:p``, ``--checkpoint-path``
    * Define the path to where the checkpoints are located. (Default: ``data``)


Configuration
-------------

Configuration of ``Trident`` is made through the configuration file, by default located at ``config/trident.json``.

Any argument that also exist as a possible configuration value in the config file will be used over the value in the configuration file for all the plugins, so the arguments exist as a sort of override to any configuration value.

The configuration file is divided into sections with the default section ``TRIDENT`` being used and the expected format should be according to the following example for configuring one runner.

.. code-block:: JSON
    :linenos:
    
    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "[plugin_id]": {
                    "path": "[plugin_path]",
                    "plugin_args": {
                        "[arg_name]": "[arg_value]"
                    },
                    "args": {
                        "[runner_args]": {
                        }
                    }
                }
            }
        }
    }


The following is a example configuration for two plugins, where the first runner instance don't store any of the produced results in a `.json` store.

.. code-block:: JSON
    :linenos:
    
    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "plugin0": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 0
                    },
                    "args": {
                        "store": {
                            "no_store": true
                        }
                    }
                },
                "plugin1": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 10
                    },
                    "args": {
                        "store": {
                            "no_store": false
                        }
                    }
                }
            }
        }
    }


The ``args`` section is optional and contain the following sections: ``daemon``, ``store``, ``runner``, ``notification`` and ``trident``.

The ``args`` section can be placed either inside each plugin definition to define specific behavior for that plugin or it can be placed outside to be defined for all of the plugins. These can also be combined to provide a general template for the plugins and specializations for certain plugins.

Example: This example shows two plugins were the global ``args`` is defined to not store any values produced by the plugins in stores on the system and at maximum use ``2`` concurrent workers. However, we have also defined ``plugin0`` to store the results produced from the plugin and store them in the folder ``data/data``.

.. code-block:: JSON
    :linenos:
    
    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "plugin0": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 0
                    },
                    "args": {
                        "store": {
                            "no_store": false,
                            "path_store": "data/data"
                        }
                    }
                },
                "plugin1": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 10
                    }
                }
            },
            "args": {
                "store": {
                    "no_store": true
                },
                "daemon": {
                    "workers": 2
                }
            }
        }
    }


The ``daemon`` and ``trident`` sections are applied as arguments for all of the plugins as they concern the general execution of the program.

The ``daemon`` section allows for the following arguments:

* ``workers``
    * The amount of workers that should be used at maximum to execute the plugins.
    * Default: ``5``

Example: 

.. code-block:: JSON
    :linenos:

    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "[plugin_id]": {
                    "path": "[plugin_path]",
                    "plugin_args": {
                        "[arg_name]": "[arg_value]"
                    },
                    "args": {
                        "[runner_args]": {
                        }
                    }
                }
            },
            "args": {
                "daemon": {
                    "workers": 5
                }
            }
        }
    }


The ``trident`` section allows for the following arguments:

* ``verbose``
    * Enable verbose logging.

* ``quiet``
    * Disable logging.

Example: Disables the output for all plugins.

.. code-block:: JSON
    :linenos:

    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "[plugin_id]": {
                    "path": "[plugin_path]",
                    "plugin_args": {
                        "[arg_name]": "[arg_value]"
                    },
                    "args": {
                        "[runner_args]": {
                        }
                    }
                }
            },
            "args": {
                "trident": {
                    "quiet": true
                }
            }
        }
    }


The ``store`` section allows for the following arguments:

* ``no_store``
    * Do not store any of the produced values in a store on the system.
* ``global_store``
    * Define the path to a global store to use for all plugins.
* ``path_store``
    * Define the path on the system where the store should be placed.
    * Default: ``data``

Example: Store values for all plugins in a global store except one runner that does not store any values.

.. code-block:: JSON
    :linenos:

    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "plugin0": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 0
                    },
                    "args": {
                        "store": {
                            "no_store": true
                        }
                    }
                },
                "plugin1": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 10
                    }
                },
                "plugin2": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 20
                    }
                }
            },
            "args": {
                "store": {
                    "global_store": "data/global.json"
                },
                "daemon": {
                    "workers": 3
                }
            }
        }
    }

The ``checkpoint`` section allows for the following arguments:

* ``checkpoint_path``
    * Specify the checkpoint path to store and load states from, if not provided the checkpoint path will be determined from the store path.
    * By not specifiying a ``checkpoint_path`` and not implementing the state methods then no checkpoint will be created.


The ``notification`` section allows for the following arguments for ``HTTP`` notifications.

* ``destination``
    * Destination to send the ``HTTP`` request to, required.
* ``method``
    * HTTP method to use for the request, either ``GET`` or ``POST``.
* ``headers``
    * Define any headers to send with the request.
* ``payload``
    * Define a payload to send with every request.
* ``include_result``
    * Include the result from the plugin in the request
    * Default, ``false``

Example: A HTTP notification named ``http-notification`` including the results from the plugin.

.. code-block:: JSON
    :linenos:

    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "plugin0": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 0
                    },
                    "args": {
                        "notification": {
                            "http-notification": {
                                "HTTP": {
                                    "method": "GET",
                                    "destination": "http://example.com",
                                    "include_results": true
                                }
                            }
                        }
                    }
                }
            }
        }
    }

The ``notification`` section allows for the following arguments for ``E-Mail`` notifications.

* ``smtp_server``
    * The SMTP server address to use, on the form of ``host:port``, required.
* ``sender``
    * The sender address, like ``name@host.com``, required.
* ``receivers``
    * The list of receivers, required.
* ``headers``
    * The headers to include in the SMTP request.
* ``subject``
    * The subject line to use for the e-mail.
    * Default: ``Trident Notification for: 'NAME'``
* ``message``
    * The message to include in all e-mails.
* ``include_result``
    * Include the result from the plugin in the request
    * Default: ``false``

Example: An e-mail notification named ``email-notification`` including the results from the plugin.

.. code-block:: JSON
    :linenos:

    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "plugin0": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 0
                    },
                    "args": {
                        "notification": {
                            "email-notification": {
                                "EMAIL": {
                                    "smtp_server": "host:port",
                                    "sender": "trident@trident.com",
                                    "receivers": ["receiver@example.com"],
                                    "subject": "Test Subject",
                                    "include_result": true
                                }
                            }
                        }
                    }
                }
            }
        }
    }

The ``runner`` section allows for the following arguments:

* ``dont_store_on_error``
    * If this is set to ``true`` then if any exceptions occur when running the plugin the runner will quit immediatly and not store the values accumulated up until that crash.
    * Default: ``false``
* ``filter_results``
    * If this is set to a list of filters in the form of regex (``re`` in ``Python``) then only the results matching any pattern will be stored.
    * Default: ``[]``

Example: Two plugins were the values of one of the plugins are stored if the runner encounters an exception and if the values match any of the filters ``[a-z]`` or ``[A-Z]``.

.. code-block:: JSON
    :linenos:

    {
        "TRIDENT": {
            "logging_level": "INFO",
            "plugins": {
                "plugin0": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 0
                    },
                    "args": {
                        "runner": {
                            "dont_store_on_error": true,
                            "filter_results": ["[a-z]", "[A-Z]"]
                        }
                    }
                },
                "plugin1": {
                    "path": "plugins.plugin",
                    "plugin_args": {
                        "value": 10
                    }
                }
            },
            "args": {
                "daemon": {
                    "workers": 2
                }
            }
        }
    }


Developing Plugins
------------------

Trident plugins are normal ``Python`` modules and the actual plugin is a class that needs to be named just as the name of the ``Python`` module, so if you have the plugin ``find_file.py`` then the class in the plugin needs to be named ``FindFile``.

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

Creating and Loading States
---------------------------

When running plugins that take some time to run it might be necessary to interrupt the execution sometimes and continue later. Therefore `Trident` supports saving and loading plugin states using checkpoints similar to data stores. The checkpoints are saved as `JSON` but the format is up to the author of the plugin as they need to decide when to save and load the state.

In order to save and load the states of the plugin the plugin needs to implement the `getter` and `setter` for `plugin_state` as described in the below minimal example.

.. code-block:: python
    :linenos:

    class FindFile:
        def __init__(self):
            self._state = None

        @property
        def plugin_state(self):
            return self._state

        @plugin_state.setter
        def plugin_state(self, state):
            self._state = state

        def execute_plugin(self, thread_event, file_name):
            # Find the file with the name file_name on the system, the starting point is in self._state
            ...


The ``getter`` (``property``) and the ``setter`` (``plugin_state.setter``) can be implemented in any way the author wants as long as the ``getter`` returns a ``JSON`` serializable object.
