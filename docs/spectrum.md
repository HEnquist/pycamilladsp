# Spectrum analysis
This class is accessed via the `spectrum` property on a `CamillaClient` instance.

It provides methods for analyzing the frequency spectrum of audio passing
through the capture or playback side.
`get_spectrum` returns a single snapshot, while `subscribe_spectrum` listens
to pushed spectrum events from the websocket server and blocks while events
are being received.

##  class: `Spectrum`
::: camilladsp.spectrum.Spectrum
