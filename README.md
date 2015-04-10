
## Gossen U180C in Python

An interface to connec to the Gossen U180C via *Modbus TCP* or via *HTTP*.
This is the LAN interface for the professional grade Gossen U189C energy meter.

### Requirements

* Python3 (I use Python 3.4)
* If you want to connect via Modbus, you need
  [pymodbus][] for Python3 (depends on [twisted][] in turn).  
  Its documentation is found [here](https://pymodbus.readthedocs.org).
* To connect via HTTP, you also need to install the [requests][] module.

[pymodbus]: https://github.com/bashwork/pymodbus/tree/python3
[twisted]: https://twistedmatrix.com
[requests]: http://docs.python-requests.org

