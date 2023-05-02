# Overview

Python library for communicating with CamillaDSP.

The main component is the `CamillaClient` class.
This class handles the communication over websocket with the CamillaDSP process.

The various commands are grouped on helper classes that are instantiated
by the CamillaClient class.
For example volume controls are handled by the `Volume` class.
These methods are accessible via the `volume` property of the CamillaClient.
Reading the main volume is then done by calling `my_client.volume.main()`.

## Command group classes
|      Class   | Property | Description |
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

