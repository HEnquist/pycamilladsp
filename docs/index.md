# Overview

Python library for communicating with CamillaDSP.

The main component is the [CamillaClient][camilladsp.CamillaClient] class.
This class handles the communication over websocket with the CamillaDSP process.

The various commands are grouped on helper classes that are instantiated
by the CamillaClient class.
For example volume controls are handled by the `Volume` class.
These methods are accessible via the `volume` property of the CamillaClient.
Reading the main volume is then done by calling `my_client.volume.main()`.

Methods for reading a value are named the same as the name of the value,
while methods for writing have a `set_` prefix.
For example the method for reading the main volume is called `main`,
and the method for changing the main volume is called `set_main`.

Example:
```py
client = CamillaClient("localhost", 1234)
client.connect()

volume = client.volume.main()
mute = client.mute.main()
state = client.general.state()
capture_levels = client.levels.capture_rms()
```

## Command group classes
|      Class   | Via property | Description |
|--------------|----------|-------------|
| [General][camilladsp.camilladsp.General] | `general` | Basics, for example starting and stopping processing |
| [Status][camilladsp.camilladsp.Status] | `status` | Reading status parameters such as buffer levels |
| [Config][camilladsp.camilladsp.Config] | `config` | Managing the configuration |
| [Volume][camilladsp.camilladsp.Volume] | `volume` | Volume controls |
| [Mute][camilladsp.camilladsp.Mute] | `mute` | Mute controls |
| [Levels][camilladsp.camilladsp.Levels] | `levels` | Reading signal levels |
| [RateMonitor][camilladsp.camilladsp.RateMonitor] | `rate` | Reading the sample rate montitor |
| [Settings][camilladsp.camilladsp.Settings] | `settings` | Websocket server settings |
| [Versions][camilladsp.camilladsp.Versions] | `versions` | Read software versions |

## All commands

### [General][camilladsp.camilladsp.General]
These commands are accessed via the [general][camilladsp.CamillaClient.general]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.General
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Status][camilladsp.camilladsp.Status]
These commands are accessed via the [status][camilladsp.CamillaClient.status]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Status
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Config][camilladsp.camilladsp.Config]
These commands are accessed via the [config][camilladsp.CamillaClient.config]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Config
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Volume][camilladsp.camilladsp.Volume]
These commands are accessed via the [volume][camilladsp.CamillaClient.volume]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Volume
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Mute][camilladsp.camilladsp.Mute]
These commands are accessed via the [mute][camilladsp.CamillaClient.mute]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Mute
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Levels][camilladsp.camilladsp.Levels]
These commands are accessed via the [levels][camilladsp.CamillaClient.levels]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Levels
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [RateMonitor][camilladsp.camilladsp.RateMonitor]
These commands are accessed via the [rate][camilladsp.CamillaClient.rate]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.RateMonitor
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Settings][camilladsp.camilladsp.Settings]
These commands are accessed via the [settings][camilladsp.CamillaClient.settings]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Settings
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Versions][camilladsp.camilladsp.Versions]
These commands are accessed via the [versions][camilladsp.CamillaClient.versions]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.camilladsp.Versions
    options:
      show_bases: false
      show_source: falses
      how_docstring_parameters: false
      show_docstring_returns: false