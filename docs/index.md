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
| [General][camilladsp.general.General] | `general` | Basics, for example starting and stopping processing |
| [Status][camilladsp.status.Status] | `status` | Reading status parameters such as buffer levels |
| [Config][camilladsp.config.Config] | `config` | Managing the configuration |
| [Volume][camilladsp.volume.Volume] | `volume` | Volume and mute controls |
| [Levels][camilladsp.levels.Levels] | `levels` | Reading signal levels |
| [RateMonitor][camilladsp.ratemonitor.RateMonitor] | `rate` | Reading the sample rate montitor |
| [Settings][camilladsp.settings.Settings] | `settings` | Websocket server settings |
| [Versions][camilladsp.versions.Versions] | `versions` | Read software versions |

## All commands

### [General][camilladsp.general.General]
These commands are accessed via the [general][camilladsp.CamillaClient.general]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.general.General
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Status][camilladsp.status.Status]
These commands are accessed via the [status][camilladsp.CamillaClient.status]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.status.Status
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Config][camilladsp.config.Config]
These commands are accessed via the [config][camilladsp.CamillaClient.config]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.config.Config
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Volume][camilladsp.volume.Volume]
These commands are accessed via the [volume][camilladsp.CamillaClient.volume]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.volume.Volume
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Levels][camilladsp.levels.Levels]
These commands are accessed via the [levels][camilladsp.CamillaClient.levels]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.levels.Levels
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [RateMonitor][camilladsp.ratemonitor.RateMonitor]
These commands are accessed via the [rate][camilladsp.CamillaClient.rate]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.ratemonitor.RateMonitor
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Settings][camilladsp.settings.Settings]
These commands are accessed via the [settings][camilladsp.CamillaClient.settings]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.settings.Settings
    options:
      show_bases: false
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false

### [Versions][camilladsp.versions.Versions]
These commands are accessed via the [versions][camilladsp.CamillaClient.versions]
property of a [CamillaClient][camilladsp.CamillaClient] instance.
::: camilladsp.versions.Versions
    options:
      show_bases: false
      show_source: falses
      how_docstring_parameters: false
      show_docstring_returns: false