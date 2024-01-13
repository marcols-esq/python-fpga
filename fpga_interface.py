import json
from pathlib import Path

from usb_interface.usb_interface import UsbInterface
from usb_interface.atlys_interface import AtlysInterface
from port_tools.port_manager import PortManager, PortList, IoPort, ClockPort

JSON_PORT_LIST_KEY = "ports"
JSON_BITFILE_PATH_KEY = "bitfile_path"
JSON_USB_INTERFACE_KEY = "fpga_interface"
JSON_ATLYS_INTERFACE_KEY = "atlys"
JSON_SUPPORTED_INTERFACE_KEYS = [JSON_ATLYS_INTERFACE_KEY]


class FpgaInterface(object):
    def __init__(self, json_config_path: Path) -> None:
        with open(json_config_path) as json_file:
            raw_json = json.load(json_file)
            if JSON_PORT_LIST_KEY not in raw_json:
                raise ValueError(
                    f'Provided JSON configuration does not contain "{JSON_PORT_LIST_KEY}" object'
                )
            self._port_manager = PortManager(raw_json[JSON_PORT_LIST_KEY])
            self._usb_interface = self._get_usb_interface(
                raw_json.get(JSON_USB_INTERFACE_KEY),
                raw_json.get(JSON_BITFILE_PATH_KEY),
            )

    def _get_usb_interface(self, json_interface_config, json_bitfile_path: Path):
        if json_interface_config == JSON_ATLYS_INTERFACE_KEY:
            return AtlysInterface(json_bitfile_path)

        print(
            "No fpga_interface specified or unknown fpga_interface in JSON config, using dummy one"
        )
        print(
            f"Currently supported fpga_interface values: {' '.join(key for key in JSON_SUPPORTED_INTERFACE_KEYS)}"
        )
        return UsbInterface()

    def get_port_list(self) -> PortList:
        return self._port_manager.get_port_list()

    def read(self, port: IoPort) -> int:
        return self._usb_interface.read(port)

    def write(self, port: IoPort, value: int) -> bool:
        return self._usb_interface.write(port, value)

    def write_clock_cycles(self, port: ClockPort, cycles: int) -> bool:
        return self._usb_interface.write_clock_cycles(port, cycles)
