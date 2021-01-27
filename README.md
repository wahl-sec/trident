# **Trident**

## **Description**
`Trident` is a asynchronous intrustion detection environment that allows for defining and running [plugins](#plugins) to scan/modify/store resources on the system. `Trident` comes pre-packaged with some [plugins](#plugins) to function as a intrusion detection system both for a host (HIDS) and the network available to the host as a network intrusion detection system (NIDS).

Trident currently allows for modules written in `Python` to act as [plugins](#plugins) using the Trident library to allow for some basic instructions.

`Trident` tries to use as little external modules as possible and allows the user to run `Trident` using only the standard library. This is done to ensure maximum compatability with hosts and to allow to focus on developing asynchronous libraries to use in the plugins. `Trident` also has the ability to use methods that rely on external libraries as well, like [`requests`](https://requests.readthedocs.io/en/master/) if preferred, for example, if the user lacks required functionality in the `Trident` plugin library functions.

For usage instructions on `Trident` please refer to the [usage](#usage) section.

## **TODO**
The `Trident` program is a quite large program considering the amount of functionality that need to be in place for the IDS to actually identify threats, so there is always more functionality that needs to be worked on. Below we have the functionality that is next in line for development, in no particular order.

- Add documentation to the `Trident` plugin library. (Medium)
- Implement plugin specific arguments allowing for example `--no-store` for a specific set of plugins. (Medium)
- Add documentation to the `Trident` program. (Medium)
- Add pytest tests for the functionality that is not yet tested. (Medium)
- Add a dashboard for `Trident` allowing the user to view the daemon metrics and results live. (Major)
- Add file system functionality to the `Trident` plugin library. (Major)
- Add event log parsing to the `Trident` plugin library. (Major)
- Add `REGEDIT` parsing to the `Trident` plugin library. (Major)
- Add system device parsing to the `Trident` plugin library. (Major)
- Add firewall parsing/altering to the `Trident` plugin library. (Major)
- Add notification system to `Trident` for Ubuntu, Windows 10. (Major)
- Add `CONTRIBUTING` documentation to the project. (Minor)
- Refactor code to follow the same pattern everywhere. (Medium)
    - Variable names should be of same format everywhere.
    - Parameter passing using keywords or not.
    - Use `_name` for "private" references.
    - Use `name_` for shadowed references.

## **Setup**
### **Requirements**
*`Trident` is tested using the versions below but might work with earlier versions as well*
- `make` >= 4.4 (If building using the `Makefile`)
- `Python` >= 3.6
    - `requests` >= 2.25.1

### **Development Requirements**
- `Python` >= 3.6
    - `pytest` >= 6.2.1
    - `wheel` >= 0.36.2
    - `setuptools` >= 51.1.2

### **Instructions**
Installing `Trident` is done using any of the following options:

- Makefile (Use standard libraries only)
    1. `make install`

- Makefile (Allow external libraries)
    1. `make install external`

- Wheel
    1. `pip install trident-VERSION.whl`

- Source
    1. `python3 setup.py install`

## **Plugins** <a name="plugins"></a>
Trident uses plugins written in `Python` to act as an IDS. The plugins need to be written in a specific format that allows Trident to control them from the daemon, this format is specified under section [Developing Plugins](#developing).

By default the plugins are written to use non-blocking operations and uses `yield` to return a generator for the plugins which allows the plugins to do operation on each result without waiting for full completion of each plugin. It is possible to just use a `return` statement instead of `yield` to wait for full execution of the plugin.

If there are any results from the plugin and these are returned to the Trident runner then `Trident` is able to store the results in the data stores specified by the user. By default these data stores are stored in the `.json` format. If the plugin is using generators to return results iteratively the result for each iteration will be stored in the data store.

### **Usage** <a name="usage"></a>

*Examples*
- `python3 -m trident` (Run the default configuration file using the `TRIDENT` section)
- `python3 -m trident -c:s DEBUG` (Use the `DEBUG` section in the configuration file)
- `python3 -m trident -s:n` (Do not store results from any `Trident` plugins)

#### **Arguments**
The arguments for `Trident` can also be displayed using the `-h`, `--help` flag.

*Required*
- `-c`, `--config`
    - The path to the `Trident` configuration file. The config file should be of format `.json`. (Default: `config/trident.json`)
- `-c:s`, `--section`
    - The section to use in the `Trident` configuration file. (Default: `TRIDENT`)

*Trident Configuration*
- `-v`, `--verbose`
    - Enable verbose logging of `Trident`
- `-q`, `--quiet`
    - Disable all logging of `Trident`
- `-w`, `--workers`
    - Define the amount of workers used by `Trident` to run plugins. If the amount of workers is set to one then `Trident` is run synchronously. (Default: `1`)

*Plugin Configuration*
- `-p:n`, `--dont-store-on-error`
    - Do not store the accumulated results if the plugin encounters an error. Default behavior is to store the behavior up until the error occured (assuming that the plugin is using generators). (Default: `False`)

*Storage Configuration*
- `-s:p`, `--path-store`
    - Define the path to where the stores are located. (Default: `data`)
- `-s:n`, `--no-store`
    - Disable the storage of results for all plugins. (Default: `False`)
- `-s:g`, `--global-store`
    - Define a path to a store used by all plugins. (Default: `None`)

#### **Configuration**
Configuration of `Trident` is made through the configuration file, by default located at `config/trident.json`.

Any argument that also exist as a possible configuration value in the config file will be used over the value in the configuration file for all the plugins, so the arguments exist as a sort of override to any configuration value.

The configuration file is divided into sections with the default section `TRIDENT` being used and the expected format should be according to the following example for configuring one runner.
```json
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
                        ...
                    }
                }
            }
        }
    }
}
```

The following is a example configuration for two plugins, where the first runner instance don't store any of the produced results in a `.json` store.
```json
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
```

The `args` section is optional and contain the following sections: `daemon`, `store`, `runner` and `trident`.

The `args` section can be placed either inside each plugin definition to define specific behavior for that plugin or it can be placed outside to be defined for all of the plugins. These can also be combined to provide a general template for the plugins and specializations for certain plugins.

Example: This example shows two plugins were the global `args` is defined to not store any values produced by the plugins in stores on the system and at maximum use `2` concurrent workers. However, we have also defined `plugin0` to store the results produced from the plugin and store them in the folder `data/data`.
```json
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
```

The `daemon` and `trident` sections are applied as arguments for all of the plugins as they concern the general execution of the program.

The `daemon` section allows for the following arguments:

* `workers`
    * The amount of workers that should be used at maximum to execute the plugins.
    * Default: `5`

Example: 
```json
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
                        ...
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
```

The `trident` section allows for the following arguments:

* `verbose`
    * Enable verbose logging.

* `quiet`
    * Disable logging.

Example: Disables the output for all plugins.
```json
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
                        ...
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
```

The `store` section allows for the following arguments:

* `no_store`
    * Do not store any of the produced values in a store on the system.
* `global_store`
    * Define the path to a global store to use for all plugins.
* `path_store`
    * Define the path on the system where the store should be placed.
    * Default: `data`

Example: Store values for all plugins in a global store except one runner that does not store any values.
```json
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
```

The `runner` section allows for the following arguments:

* `dont_store_on_error`
    * If this is set to `true` then if any exceptions occur when running the plugin the runner will quit immediatly and not store the values accumulated up until that crash.
    * Default: `false`

Example: Two plugins were the values of one of the plugins are stored if the runner encounters an exception.
```json
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
                        "dont_store_on_error": true
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
```

### **Developing Plugins** <a name="developing"></a>
`Trident` plugins are normal `Python` modules and the actual plugin is a class that needs to be named just as the name of the `Python` module, so if you have the plugin `find_file.py` then the class in the plugin needs to be named `FindFile`.

The entry point of the plugin is always `execute_plugin` so when defining any new plugin this method needs to be present. See example below.

```python
class FindFile:
    def execute_plugin(self, thread_event, file_name):
        # Find the file with the name file_name on the system
        ...
```

#### **Plugin Library**
The `Trident` plugin library offers functionality to do some common operations on the host system, for example, walking the file system to find files, opening ports, sending packets and more.

The `Trident` plugin library uses its own library to implement crucial functionality like `TCP`, `UDP`, `ICMP` and more to not rely on external modules. These are available to anyone wishing to extend the `Trident` plugin library with their own functionality.

The library tries to implement each functionality using primarily generators to allows for better asynchronous behavior. For each function that return a generator there is also a iterative version that returns the finished operation, the name of the iterative version is usually the original name with `_iter` appended to it.

#### **Variables**
By default `Trident` tries to pass the `thread_event` parameter to the plugin, this is of type `Event` from the `threading` library and is used to allow the system to halt the execution of `Trident` with keyboard interrupt. Note that the plugin needs to implement periodic checks of this variable using `thread_event.is_set()` in order for this to work. If the plugin does not implement the check then if `Trident` is passed an interrupt by the system then `Trident` will not be able to exit until the plugin operations finish.

`Trident` allows the user to pass any initial parameters to the plugin by defining the `args` key in the plugin configuration followed by the value. `Trident` will try to pass each variable found in the `args` section of the plugin configuration to the `execute_plugin` method, so the method needs to have these parameters defined as well.
