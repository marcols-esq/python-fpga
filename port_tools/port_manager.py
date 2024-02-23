from collections.abc import Iterator
import json

from . import port_defs
from .port import IoPort, ClockPort


class PortList(dict):
    def __getattr__(self, __key):
        item = self.get(__key)
        if item is None:
            raise KeyError(f"Port {__key} is not defined in this PortList")
        return item
    
    def __iter__(self) -> Iterator:
        yield from self.values()



class PortManager(json.JSONDecoder):
    def __init__(self, json_port_config=None) -> None:
        self._ports = PortList()
        if json_port_config is not None:
            self._parse_ports(json_port_config)

    def _parse_ports(self, raw_json):
        for port_data in raw_json['ports']:
            if port_data.get(port_defs.IS_CLOCK_KEY):
                self._ports[port_data.get(port_defs.NAME_KEY)] = ClockPort(
                    name=port_data.get(port_defs.NAME_KEY),
                    address=port_data.get(port_defs.ADDRESS_KEY),
                )
            else:
                self._ports[port_data.get(port_defs.NAME_KEY)] = IoPort(
                    name=port_data.get(port_defs.NAME_KEY),
                    address=port_data.get(port_defs.ADDRESS_KEY),
                    clock_port=port_data.get(port_defs.IS_CLOCK_KEY),
                    direction=port_data.get(port_defs.DIRECTION_KEY),
                    bit_width=port_data.get(port_defs.BIT_WIDTH_KEY),
                    enable_signal=port_data.get(port_defs.INOUT_ENABLE_SIGNAL),
                    enable_signal_active=port_data.get(port_defs.INOUT_ENABLE_SIGNAL_ACTIVE)
                )

    def get_port_list(self):
        return self._ports
