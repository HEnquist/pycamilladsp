# Overview

Python library for communicating with CamillaDSP.

The main component is the [CamillaClient][camilladsp.CamillaClient] class.
This class handles the communication over websocket with the CamillaDSP process.

The various commands are grouped on helper classes that are instantiated
by the CamillaClient class.
For example volume and mute controls are handled by the `Volume` class.
These methods are accessible via the `volume` property of the CamillaClient.
Reading the main volume is then done by calling `my_client.volume.main_volume()`.

Methods for reading a value are named the same as the name of the value,
while methods for writing have a `set_` prefix.
For example the method for reading the main volume is called `main_volume`,
and the method for changing the main volume is called `set_main_volume`.

Example:
```py
client = CamillaClient("localhost", 1234)
client.connect()

volume = client.volume.main_volume()
mute = client.volume.main_mute()
state = client.general.state()
capture_levels = client.levels.capture_rms()
```

Subscriptions are also available for streaming updates. For example,
`client.levels.subscribe_signal_levels(...)` can be used to receive signal
level events, and `client.general.subscribe_state(...)` can be used to
receive processing state changes. Subscription calls block while listening for
events, so use a separate client connection for each concurrent subscription.

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
This group also includes `subscribe_state`, which listens for processing state
change events.
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
This group also includes `subscribe_signal_levels`, which listens for signal
level events on the selected side.
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
      show_source: false
      show_docstring_parameters: false
      show_docstring_returns: false