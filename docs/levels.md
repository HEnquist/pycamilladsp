# Level monitoring
This class is accessed via the `levels` property on a `CamillaClient` instance.

It provides methods for reading signal levels.
It also includes `subscribe_signal_levels` for listening to signal level
events from the websocket server, and `subscribe_vu_levels` for listening to
pre-smoothed, rate-limited VU meter events. Subscription methods block while
events are being received.

##  class: `Levels`
::: camilladsp.levels.Levels