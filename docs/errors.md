
# Errors

The custom exception [CamillaError][camilladsp.datastructures.CamillaError] is raised when CamillaDSP replies to a command with an error message. The error message is given as the message of the exception.

Different exceptions are raised in different situations. Consider the following example:
```python
from camilladsp import CamillaClient, CamillaError
cdsp = CamillaClient("127.0.0.1", 1234)

myconfig = # get a config from somewhere
try:
    cdsp.connect()
    cdsp.config.validate(myconfig)
except ConnectionRefusedError as e:
    print("Can't connect to CamillaDSP, is it running? Error:", e)
except CamillaError as e:
    print("CamillaDSP replied with error:", e)
except IOError as e:
    print("Websocket is not connected:", e)
```
- `ConnectionRefusedError` means that CamillaDSP isn't responding on the given host and port.
- `CamillaError` means that the command was sent and CamillaDSP replied with an error.
- `IOError` can mean a few things, but the most likely is that the websocket connection was lost.
  This happens if the CamillaDSP process exits or is restarted.

## CamillaError
::: camilladsp.datastructures.CamillaError